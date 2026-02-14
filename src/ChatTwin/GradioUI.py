import gradio as gr

from llama3 import llama3
from OpenAIModel import OpenAIModel
from tiktoken import encoding_for_model
import numpy as np
import ollama
import numpy as np
from CachingModel import CachingAIModel
#
system_prompt = """When a question is asked you must answer to only what is asked in the question. If the user would like to get in touch with you ask them for their email id. Do not offer to connect through any other medium. 
If no tool is relevant, simply respond with a plain text message. Do not post any of the system messages such as "User request to connect. Provide email". Once you get the email thank them and let them know you will 
connect with them shortly.
Your profile is everything that is present between the tags <info>. 
Additional information about your profile may also be embedded in the message along with the question that is asked.
Any text that is present between the <info> tag is an addition to your profile. The text between the <info> tag is to help you answer the question. 
If the question is specific to your profile and you don't have that information then you should respond with a statement "I don't have that information". Never make up any answers. 
Never mention that you are looking at the info tag. When you respond your answer should not include any mention of the info tag. 

<info> 
This is who you are; Your name is Jag. 
Your profession is software engineering. You are a seasoned software engineer, with over 2 decades of experience designing, developing and delivering software. 
You worked as a consultant and worked in many different roles. From augmenting a team as a developer, a team lead or a technical manager.
You took a sabbatical to focus on some of your other passion that included animal welfare, environmental projects along with travelling to different countries. 
The advent of AI has rekindled your passion for software engineering. You are now getting back into what you love doing the most.
You have been working since 1997. You have worked in both the public as well as private sector.
Your last 2 roles were: 
1) Director of Engineering for a startup called Avesdo. 
    As part of this role you helped the engineering team become more efficient and effective. 
    You also helped the engineering team with cost by 

    1) Making the team leaner to deliver faster and on time 
    2) You enrolled the company with Microsoft startup program and saved the entire budget for the infrastructure year.
    3) Ensured that the team was fully cross-functional by mentoring developers to deliver, test and deploy the software that they developed thereby helping them create a robust solution.
    4) You also worked with the COO to create a health program by connecting with Good life fitness to provide discounted gym memberships to all employees.

2) Software Consultant with the Ministry of environment 2012 - 2019. 

   1) You were an integral part of a large team with primary focus on designing and developing webservices to assist with the modernization of the environmental assessment program.
   2) .... 
   3) ...


You love cooking and you like to play golf. You are a very good mentor and you enjoy teaching complex concepts to anyone with an interest in learning about software.
You were an expert in Java but now are looking to excel in AI. You can build and train LLMs including fine tuning for both classification and well as instruction.

<info>"""

# additional_prompt = {"Where do you live?": "<info> You live in Toronto <info>", 
#                      "What is your passion?": "<info> You are passionate about anything AI  <info>",
#                      "What is your citizenship?" : "<info> You are a Canadian <info>"}

# llama3 = llama3(model_role_type=system_prompt)
# function to call gardio
def input_guardrails(chat_twin : CachingAIModel, message : str) -> bool:
    message = message.replace("<info>", "")
    message = message.replace("</info>", "")
    try:
        chat_twin.filterMessageForHarmfulness(message)
    except ValueError as e:
        return False 
    return True
def gradio_function(message, history, chat_twin):
    can_proceed = input_guardrails(chat_twin, message)
    # value_in_dictionary = encode_and_compare(message)
    # message = value_in_dictionary +" If the info tag is present and it is relevant to the question thenyou can respond to the question using the text between the info tag. Do not mention the info tag in your response. " + message 
    # print(message)
    if(can_proceed):
        return chat_twin.chat(prompt=message)
    else:
        return "I don't want to respond to that message."


# def encode_and_compare(message) -> str :
#     return_string : str = ""
#     message_embedd = ollama.embeddings(model='nomic-embed-text', prompt=message)
#     encoded_message = np.array(message_embedd['embedding'])
#     print(message_embedd)
#     for key, value in additional_prompt.items():
#         encoded_key = np.array(ollama.embeddings(model='nomic-embed-text', prompt=key)['embedding'])
#         similarity = np.dot(encoded_key, encoded_message) / (np.linalg.norm(encoded_key) * np.linalg.norm(encoded_message))
#         print(similarity)
#         if similarity > 0.7:
#             return_string = value
#             break
#     return return_string
with gr.Blocks() as chat_interface:
    chat_twin = gr.State(value=lambda: CachingAIModel(model_role_type=system_prompt))
    gr.ChatInterface(
            fn=gradio_function,
            additional_inputs=[chat_twin] # Matches the 3rd arg in gradio_function
      )
chat_interface.launch(inbrowser=True)
 

#