import streamlit as st
import os
import requests
import json
from datetime import datetime
import pandas as pd


invoke_url = "https://cejctqvrrf.execute-api.us-west-2.amazonaws.com/prod"
api = invoke_url + '/chat_bot?query='

index = "retail_product_info_0913"

personalize_invoke_url = 'https://4ky8wvi8pj.execute-api.us-west-2.amazonaws.com/prod'
ads_invoke_url = "https://gk3ux28m6f.execute-api.us-west-2.amazonaws.com/prod"
ads_invoke_url += '/get_item_ads?'

product_invoke_url = 'https://z9mkbx0zok.execute-api.us-west-2.amazonaws.com/prod'
product_invoke_url += '/product_recommendation?query='

user_info_url = 'https://k9xut1huq4.execute-api.us-west-2.amazonaws.com/prod'
user_info_url += '/user_info?user_id='

digital_url = "https://eb8lfyfi06.execute-api.us-west-2.amazonaws.com/default/set_instant_metadata"


# App title
st.set_page_config(page_title="aws intelligent recommendation solution")

def clear_chat_history():
    st.session_state.messages = [{"role": "assistant", "content": "How may I assist you today?"}]
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    st.session_state.sessionId = 'ir'+str(timestamp)
    st.session_state.recommendationItemId = []
    invoke_digital('Hello,How may I assist you today?')

def get_user_info(user_id):
    url = user_info_url + str(user_id)
    print('get_user_info url:',url)
    response = requests.get(url)
    result = response.text
    result = json.loads(result)
    
    print('user info result:',result)

    user_base = result['user_base']
    user_history = result['user_history']

    user_age = user_base['age']
    user_gender = user_base['gender']
    user_info = 'User info: ' + str(user_age) + ' years old, ' + user_gender + ';'
    user_history_df = pd.DataFrame(user_history)
    st.write(user_info)
    st.write('User behavior history:')
    st.dataframe(user_history_df,
                 column_order=('category_2','price','event_type'),
                 column_config={'category_1':'category 1','category_2':'category 2'})

with st.sidebar:
    st.title('AWS Intelligent Shopping Guide Solution')
    # st.subheader('Models and parameters')
    # model = st.radio("Choose a model",('llama2', 'chatgpt'))
    model = 'llama2'
    # st.write("### Choose the number of conversation rounds to make recommendation")
    step = st.radio("Choose the number of conversation rounds to make recommendation",('2','3','4','5'))
    item_num = st.slider('Select the number of recommended items:', 1, 3, 1)
    st.sidebar.button('Clear Chat History', on_click=clear_chat_history)

    # st.write("### Choose a User")
    user_id = st.slider('Select a user ID:', 1, 6000, 1)
    if st.sidebar.button('Get user information'):
        get_user_info(user_id)


def invoke_digital(text,image="https://d24aerznc266jr.cloudfront.net/material/image/7979027.jpg"):
    now = datetime.now()
    timestamp = str(int(datetime.timestamp(now)))
    print('invoke_digital timestamp:',timestamp)
    body={
      "id": timestamp,
      "image_url": image,
      # "image_url": "https://d24aerznc266jr.cloudfront.net/material/image/7979027.jpg",
      "text": text,
      "random_id": timestamp,
      "character": "rp_emma_female_white",
      "scene": "screen",
      "voice": "US-En-Female",
      "action": "Talk1",
      "user_id": "VR-demo",
      "item_id": "item1",
      "voice_speed": "medium",
      "vr_module": "0001",
      "camera": "front_stand"
    }
    digital_response = requests.post(digital_url,json=body)
    print('digital_response:',digital_response)


st.write("## Just For You")

# Store LLM generated responses
if "messages" not in st.session_state.keys():
    st.session_state.messages = [{"role": "assistant", "content": "Hello,How may I assist you today?"}]
    now = datetime.now()
    timestamp = datetime.timestamp(now)
    st.session_state.sessionId = 'ir'+str(timestamp)
    st.session_state.recommendationItemId = []
    invoke_digital('Hello,How may I assist you today?')

# Display or clear chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])



# Function for generating LLaMA2 response
def generate_llama2_response(prompt,task,top_k=1):

    url = api + prompt
    url += ('&task='+task)
    url += ('&session_id='+st.session_state.sessionId)
    url += ('&llm_modle='+model)
    url += ('&index='+index)
    url += ('&top_k='+str(top_k))

    print('url:',url)
    response = requests.get(url)
    result = response.text
    result = json.loads(result)
    
    print('chat result:',result)
    answer = result['answer']
    return answer


def get_product_recommendation(query,user_id=1,top_k=1,filter_item_id=[]):
    
    url = product_invoke_url + query
    url += ('&index='+index)
    url += ('&user_id='+str(user_id))
    url += ('&top_k='+str(top_k))
    if len(filter_item_id) > 0:
        url += ('&item_filter_id='+','.join(filter_item_id))
    url += ('&llm_embedding_name=meta-textgeneration-llama-2-7b-f-2023-07-19-06-07-05-430')

    print('url:',url)
    response = requests.get(url)
    result = response.text
    result = json.loads(result)
    
    print('product result:',result)
    products = result['products']
    top_item_ids_str = result['top_item_ids_str']

    image_path_list = []
    item_id_list = []
    if len(products) > 0:
        for product in products:
            category = product['category']
            image = product['image']
            image_path = 'https://d3j4fy1ccpxvdd.cloudfront.net/'+category+'/'+image
            image_path_list.append(image_path)
            item_id_list.append(product['id'])
        # product_ad_str = result['ad_response']
    return top_item_ids_str,image_path_list,item_id_list

def get_item_ads(top_item_ids_str,user_id=1):
    url = ads_invoke_url
    url += ('item_id_list='+top_item_ids_str)
    url += ('&user_id='+str(user_id))
    # url += ('&llm_embedding_name=meta-textgeneration-llama-2-7b-f-2023-07-19-06-07-05-430')

    print('get_item_ads url:',url)
    response = requests.get(url)
    result = response.text
    result = json.loads(result)
    
    print('product result:',result)
    ads_response = result['item_ads']
    return ads_response

def item_ads_processor(item_ad):
    return item_ad.split('\n\n')[1]

# User-provided prompt
if prompt := st.chat_input():
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

# Generate a new response if last message is not from assistant
if st.session_state.messages[-1]["role"] != "assistant":
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            task = "chat"
            if len(st.session_state.messages) >= int(step)*2:
                task = 'summarize'
            placeholder = st.empty()
            # try:
            if task == "chat":
                response = generate_llama2_response(prompt,task)
                placeholder.markdown(response)
                invoke_digital(response)
            elif task == 'summarize':
                answer = generate_llama2_response(prompt,task)
                print('intention:',answer)
                top_item_ids_str,image_path_list,item_id_list = get_product_recommendation(answer,user_id=user_id,top_k=3,filter_item_id=st.session_state.recommendationItemId)
                st.session_state.recommendationItemId.extend(item_id_list)
                item_ads = get_item_ads(top_item_ids_str)
                if item_ads.find('Commodity') > 0:
                    item_ads_list = item_ads.split('Commodity')
                elif item_ads.find('Product') > 0:
                    item_ads_list = item_ads.split('Product')
                
                print("item_ads_list len:",len(item_ads_list))
                print("image_path_list len:",len(image_path_list))
                if item_num == 3:
                    col1, col2, col3 = st.columns(3)
                    with col1:
                       st.write(item_ads_processor(item_ads_list[1]))
                       # image0 = Image.open(image_path_list[0])
                       st.image(image_path_list[0])
                       st.write('http://d2qogd6e3vaci5.cloudfront.net/#/product/'+item_id_list[0])

                    with col2:
                       st.write(item_ads_processor(item_ads_list[2]))
                       # image1 = Image.open(image_path_list[1])
                       st.image(image_path_list[1])
                       st.write('http://d2qogd6e3vaci5.cloudfront.net/#/product/'+item_id_list[1])

                    with col3:
                       st.write(item_ads_processor(item_ads_list[3]))
                       # image2 = Image.open(image_path_list[2])
                       st.image(image_path_list[2])
                       st.write('http://d2qogd6e3vaci5.cloudfront.net/#/product/'+item_id_list[2])
                elif item_num ==2:
                    col1, col2 = st.columns(2)
                    with col1:
                       st.write(item_ads_processor(item_ads_list[1]))
                       # image0 = Image.open(image_path_list[0])
                       st.image(image_path_list[0])
                       st.write('http://d2qogd6e3vaci5.cloudfront.net/#/product/'+item_id_list[0])
                    with col2:
                       st.write(item_ads_processor(item_ads_list[2]))
                       # image1 = Image.open(image_path_list[1])
                       st.image(image_path_list[1])
                       st.write('http://d2qogd6e3vaci5.cloudfront.net/#/product/'+item_id_list[1])
                elif item_num ==1:
                   st.write(item_ads_processor(item_ads_list[1]))
                   st.image(image_path_list[0])
                   st.write('http://d2qogd6e3vaci5.cloudfront.net/#/product/'+item_id_list[0])
                else:
                    st.write("Sorry, We can't find that product!")
                response = item_ads_processor(item_ads_list[1])
                invoke_digital(item_ads_processor(item_ads_list[1]),image_path_list[0])


            # except:
            #     placeholder.markdown("Sorry,please try again!")
    message = {"role": "assistant", "content": response}
    st.session_state.messages.append(message)
