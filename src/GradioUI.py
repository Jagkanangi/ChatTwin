import gradio as gr
import ollama
import os
from Models.ChatTwinModel import ChatTwin
import numpy as np
from vo.Models import SessionState
from vo.MyBio import mybio
#
system_prompt : str = mybio["text"]

# 

# additional_prompt = {"Where do you live?": "<info> You live in Toronto <info>", 
#                      "What is your passion?": "<info> You are passionate about anything AI  <info>",
#                      "What is your citizenship?" : "<info> You are a Canadian <info>"}

# llama3 = llama3(model_role_type=system_prompt)
# function to call gardio
def input_guardrails(chat_twin : ChatTwin, message : str) -> tuple[bool, str]:
    message = message.replace("<info>", "")
    message = message.replace("</info>", "")
    can_continue : bool = True
    err_message : str = "No anomally detected."
    try:
        chat_twin.filterMessageForHarmfulness(message)
    except ValueError as e:
        can_continue = False
        err_message = "Harmful or abusive content detected in message."
    if(len(message) > 500):
        can_continue = False
        err_message = "Message is too long. If you want to know more about me, please give me your email and optionally a phone number. "
    if(chat_twin.num_calls > 10):
        can_continue = False
        err_message = "I know you would like to know more about me cause I am that interesting. Please give me your email and optionally a phone number and I will get in touch with you"


    
    
    return (can_continue, err_message) # This line was already there, but the previous return True was removed.
def gradio_function(message, history, session_state):
    chat_twin = session_state.get_from_session(SessionState.MODEL_KEY)
    (can_proceed, err_message)= input_guardrails(chat_twin, message)
    # value_in_dictionary = encode_and_compare(message)
    # message = value_in_dictionary +" If the info tag is present and it is relevant to the question thenyou can respond to the question using the text between the info tag. Do not mention the info tag in your response. " + message 
    # print(message)
    return_str = ""
    if(can_proceed):
        return_str = chat_twin.chat(prompt=message)
    else:
        return_str = err_message
    return return_str


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

def create_initial_state():
    # This function runs EVERY TIME a new user opens the page
    new_session = SessionState()
    new_session.add_to_session(
        SessionState.MODEL_KEY, 
        ChatTwin(model_role_type=system_prompt)
    )
    return new_session

with gr.Blocks() as chat_interface:
    state_object = gr.State(value=create_initial_state)
    
    gr.ChatInterface(
            fn=gradio_function,
            additional_inputs=[state_object] # Matches the 3rd arg in gradio_function
      )
if __name__ == "__main__":
    chat_interface.launch(inbrowser=True)
 

#