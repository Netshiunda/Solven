#Python libraries that we need to import for our bot
import random
import os
from flask import Flask, request
from pymessenger.bot import Bot
from newspaper import Article
import random
import string
#import nltk
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# Get the article
article = Article('https://www.solvency.co.za/flexible-insurance-cover.html')
article.download()
article.parse()
article.nlp()
article_text = article.text

# Print the article text
#print(article_text)
text = article_text
sentence_list = nltk.sent_tokenize(text) # list of sentences

app = Flask(__name__)
ACCESS_TOKEN =  os.environ['ACCESS_TOKEN']
VERIFY_TOKEN = os.environ['VERIFY_TOKEN']
bot = Bot(ACCESS_TOKEN)

# Exit list
exit_list = ['exit','see you later', 'bye','quit', 'break']

# User's greetings
user_greetings = ['hi','hey','hello','hola','greetings','wassup']

#We will receive messages that Facebook sends our bot at this endpoint 
@app.route("/", methods=['GET', 'POST'])
def receive_message():
    if request.method == 'GET':
        """Before allowing people to message your bot, Facebook has implemented a verify token
        that confirms all requests that your bot receives came from Facebook.""" 
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    #if the request was not get, it must be POST and we can just proceed with sending a message back to user
    else:
        # get whatever message a user sent the bot
        output = request.get_json()
        print(output)
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                if message.get('message'):
                    #Facebook Messenger ID for user so we know where to send response back to
                    recipient_id = message['sender']['id']
                    if message['message'].get('text'):
                        if message['message']['text'].lower() in exit_list:
                            response_sent_text = 'Chat with you later' 
                        elif message['message']['text'].lower() in user_greetings:
                            response_sent_text = greeting_response(message['message']['text'])
                        else:
                            response_sent_text = bot_response(message['message']['text'])
                        send_message(recipient_id, response_sent_text)
                    #if user sends us a GIF, photo,video, or any other non-text item
                    if message['message'].get('attachments'):
                        response_sent_nontext = bot_response(message['message']['text'])
                        send_message(recipient_id, response_sent_nontext)
    return "Message Processed"


def verify_fb_token(token_sent):
    #take token sent by facebook and verify it matches the verify token you sent
    #if they match, allow the request, else return an error 
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'

# Create a function to return a random greeting response to a users greeting
def greeting_response(text):
    text = text.lower()

    # Bot's greeting response
    bot_greetings = ['howdy','hi','hey','hello','hola']
    
    # User's greetings
    user_greetings = ['hi','hey','hello','hola','greetings','wassup']

    # Return a randomly choosen response from bot

    for word in text.split():
        if word in user_greetings:
            return random.choice(bot_greetings) 

# Index sort function based on similarity in descending order
def index_sort(list_var):
    length = len(list_var)
    list_index = list(range(0,length))
    
    x = list_var
    for i in range(length):
        for j in range(length):
            if x[list_index[i]] > x[list_index[j]]:
                
                # Swap
                temp = list_index[i]
                list_index[i] = list_index[j]
                list_index[j] = temp

    return list_index


# Create the bots response

def bot_response(user_input):
    user_input = user_input.lower()
    sentence_list.append(user_input)
    bot_response = ''
    # create count matrix
    cm = CountVectorizer().fit_transform(sentence_list)
    # compare the last cm entry
    similarity_scores = cosine_similarity(cm[-1],cm)
    # Reduce the dimensinality
    similarity_scores_list = similarity_scores.flatten()
    index = index_sort(similarity_scores_list)
    #print(similarity_scores_list)
    index = index[1:]
    response_flag = 0

    j = 0

    for i in range(len(index)):
        if similarity_scores_list[index[i]] > 0.0:
            bot_response = bot_response + ' ' + sentence_list[index[i]]
            response_flag = 1
            j = j + 1
        if j > 2:
            break
    #print(sentence_list)
    if response_flag == 0 :
        bot_response = bot_response + ' ' + 'I apologize, I do not understand.'
    
    sentence_list.remove(user_input)

    return bot_response


#chooses a random message to send to the user
def get_message():
    sample_responses = ["You are stunning!", "We're proud of you.", "Keep on being you!", "We're greatful to know you :)"]
    # return selected item to the user
    return random.choice(sample_responses)

#uses PyMessenger to send response to user
def send_message(recipient_id, response):
    #sends user the text message provided via input response parameter
    bot.send_text_message(recipient_id, response)
    return "success"

if __name__ == "__main__":
    app.run()