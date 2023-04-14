import re

import streamlit as st
import dirtyjson
import os
import os
from langchain.llms import OpenAI
from langchain.chat_models import ChatOpenAI
import json
from langchain import PromptTemplate
from langchain.chains import LLMChain, SimpleSequentialChain  # import LangChain libraries
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate
from langchain.utilities import GoogleSearchAPIWrapper
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]
os.environ["GOOGLE_CSE_ID"] = st.secrets["GOOGLE_CSE_ID"]
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]

llm = OpenAI(temperature=0.9, model_name="gpt-3.5-turbo")
chat = ChatOpenAI(model_name="gpt-3.5-turbo")

st.write("# Let me find a perfect gift for you on Amazon!")
request = st.text_input("Give details about recipient or what are you looking for.",
                        placeholder="Gift for my spouse, she likes walking")
# request = st.session_state.request
if not request:
    exit(0)
# st.write(request)

# Chain 1, get list of ideas
system_message_1 = """You are an owner of the biggest gift shop in the world. You know your business inside out and 
can find a perfect gift for anybody. You are going to be asked to provide 3 best gift ideas for the given request.
"""
template1 = "Please help me find a gift for the following request: '{request}'"

prompt_template1 = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(system_message_1),
        HumanMessagePromptTemplate.from_template(template1)
    ])
get_ideas_chain = LLMChain(llm=chat, prompt=prompt_template1)

# Chain 2, get json with ideas
system_message_2 = """You are experienced developer. You got a text with some gift ideas, you need to transform it to json 
format like that:
ideas: ["idea1", "idea2", "idea3"]

Example:
Input:
Based on the information provided, here are three gift ideas:\n\n1. Fitness tracker: A fitness tracker is a great gift for someone who enjoys walking. It can help your spouse keep track of their steps, distance, and calories burned.\n\n2. Walking shoes: A good pair of walking shoes is essential for anyone who enjoys walking. You can choose a comfortable and stylish pair that your spouse will love.\n\n3. Personalized water bottle: Staying hydrated is important when walking, and a personalized water bottle is a great way to make sure your spouse always has water on hand. You can customize it with your spouse's name or a special message.\n\nDo you need more information or are there any specific details I should know about?
Output:
ideas: ["fitness tracker", "Walking shoes", "Personalized water bottle"]

Example:
Input:
How about a new pair of comfortable walking shoes or a Fitbit to track her steps and progress? Another idea could be a subscription to a hiking or walking trail guidebook or a membership to a local nature park or trail.
Output:
ideas: ["walking shoes", "Fitbit", "hiking or walking trail guidebook", "membership to a local nature park or trail"]
"""
template2 = "Transform to json the following statement with ideas: {statement}"

prompt_template2 = ChatPromptTemplate.from_messages(
    [
        SystemMessagePromptTemplate.from_template(system_message_2),
        HumanMessagePromptTemplate.from_template(template2)
    ])

transform_json_chain = LLMChain(llm=llm, prompt=prompt_template2)

get_ideas_json_chain = SimpleSequentialChain(
    chains=[get_ideas_chain, transform_json_chain],
    verbose=True
)

list_of_ideas_raw = get_ideas_json_chain.run(request)

ideas_list = []

try:
    ideas_list = json.loads(list_of_ideas_raw)["ideas"]
except:
    pattern = r'(\[.*?\])'
    result = re.search(pattern, list_of_ideas_raw)
    ideas_list_string = result.group(1)
    print(f"list prepared for json parsing: {ideas_list_string}")
    ideas_list = json.loads(ideas_list_string)
    print(f"parsed list: {ideas_list}")

st.success(f"Here is a list of ideas: {ideas_list}")

# st.write(f"Here is a list of gift ideas: {ideas_list}.")
st.write(f"Let me find best relevant items on Amazon...")

# Chain 3 Search on Amazon
search = GoogleSearchAPIWrapper()


def clean_json_string(input_string):
    # Replace invalid escape sequences with valid ones
    input_string = re.sub(r'\\x', r'\\u00', input_string)
    return input_string


for idea in ideas_list:
    print(f"processing idea: {idea}")
    search_results = search.results(idea, num_results=10)

    search_results_only_asin_links = [{
        # drop 'snippet' here because it's failing json parser sometime
        "link": x["link"],
        "title": x["title"]
    } for x in search_results if "/dp/" in x["link"]]
    # print(f'search_results_only_asin_links: {search_results_only_asin_links}')
    if not search_results_only_asin_links:
        continue

    # Chain 4 choose best
    system_message_4 = """You are an experienced amazon shopper and know people very well. You would need to pick best 
    gift from the list of ideas for a given request. Response in the same format as a json array.
    """
    template_4 = """
    Here is a list of available items: {search_results}. Choose 2 which fit best for the following request: {request}. 
    Return only json array.
    """

    prompt_template_4 = PromptTemplate(
        template=template_4,
        input_variables=["search_results", "request"]
    )
    prompt_4 = prompt_template_4.format(search_results=str(search_results_only_asin_links), request=request)

    best_ideas_only = chat([
        SystemMessage(content=system_message_4),
        HumanMessage(content=prompt_4)
    ])
    print(f"best ideas string: {best_ideas_only.content}")
    cleaned_best_ideas_string = clean_json_string(best_ideas_only.content)
    print(f"cleaned best ideas string: {cleaned_best_ideas_string}")
    best_ideas_list = dirtyjson.loads(cleaned_best_ideas_string)
    print(f"parsed best ideas: {best_ideas_list}")
    if not best_ideas_list:
        continue

    st.write(f"# Idea: {idea}\n")
    st.write("\n\n".join(["\n".join([x["title"], x["link"]]) for x in best_ideas_list]))
    st.write("\n")
