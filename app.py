# Modules
from itertools import count
import pyrebase #Python Wrapper of Firebase
import streamlit as st
from datetime import datetime
from streamlit.components.v1 import html
import pickle 
import requests
import pandas as pd

# Configuration Key
firebaseConfig = {
    'apiKey': "AIzaSyCveVTigQ0-KaPN_PQAReT-e_NzLAN7odo",
    'authDomain': "movflix-streamlit-iwp.firebaseapp.com",
    'projectId': "movflix-streamlit-iwp",
    'storageBucket': "movflix-streamlit-iwp.appspot.com",
    'messagingSenderId': "478356758013",
    'appId': "1:478356758013:web:7a69e4415fb1bfd90ecd94",
    'measurementId': "G-LFTL9EVB89",
    'databaseURL': "https://movflix-streamlit-iwp-default-rtdb.firebaseio.com/",
    
}
# Firebase Authentication
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Database
db = firebase.database()
storage = firebase.storage()
st.sidebar.title("MovFlix")

# Authentication
choice = st.sidebar.selectbox('Just Select : SignIn / SignUp', ['SignIn', 'SignUp'])

# Obtain User Input for email and password
email = st.sidebar.text_input('Please enter your email address')
password = st.sidebar.text_input('Please enter your password',type = 'password')


### THE RECOMMENDATION ENGINE PART
# api key of TMDB
my_api_key = '4051077e7188c536fc7feb16b656bbd0'

def fetch_poster(movie_id):
    print("MID - ",movie_id)
    response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US'.format(movie_id,my_api_key))
    data = response.json()
    return 'https://image.tmdb.org/t/p/w500/'+data['poster_path']

def get_genere(movie_id):
    response = requests.get('https://api.themoviedb.org/3/movie/{}?api_key={}&language=en-US'.format(movie_id,my_api_key))
    data = response.json()
    return data['genres'][0]['name']

def recommend(movie, movies_df, similarity):
    movie_index = movies_df[movies_df['title'] == movie].index[0] #Way to get index with name
    distances = similarity[movie_index]
    movies_list = sorted(list(enumerate(distances)),reverse = True, key = lambda x : x[1])[1:6]
    #as top is the 1 and its the same movie
    
    recommended_movies = []
    recommended_movies_posters = []
    recommended_movies_genre = []
    for i in movies_list :
        movie_id = movies_df.iloc[i[0]].movie_id #here u get movie id - to see look at iloc 
        #fetch poster from an API
        recommended_movies.append(movies_df.iloc[i[0]].title)
        recommended_movies_posters.append(fetch_poster(movie_id))
        recommended_movies_genre.append(get_genere(movie_id))

    return recommended_movies,recommended_movies_posters,recommended_movies_genre 



# App 
original_title = '<p style="color:Red; font-size:350%; text-align:center">MovFlix</p>'
st.markdown(original_title, unsafe_allow_html=True)

# Sign up Block
if choice == 'SignUp':
    user_handle = st.sidebar.text_input('Please input your app user_handle name', value='Default')
    name = st.sidebar.text_input('Please enter your name')
    country = st.sidebar.text_input('Please enter your country')
    state = st.sidebar.text_input('Please enter your state')
    city = st.sidebar.text_input('Please enter your city')
    submit = st.sidebar.button('Create my account')

    if submit:
        user = auth.create_user_with_email_and_password(email, password)
        st.success('Your account is created suceesfully!')
        st.balloons()
        # Sign in
        user = auth.sign_in_with_email_and_password(email, password)
        db.child(user['localId']).child("user_handle").set(user_handle)
        db.child(user['localId']).child("ID").set(user['localId'])
        db.child(user['localId']).child("name").set(name)
        db.child(user['localId']).child("country").set(country)
        db.child(user['localId']).child("state").set(state)
        db.child(user['localId']).child("city").set(city)
        currTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        db.child(user['localId']).child("Timestamp").set(currTime)

        st.title('Welcome ' + name  +' aka '+ user_handle)
        st.info('Now You may Login via login drop down option.')


# Login Block
if choice == 'SignIn':
    login = st.sidebar.checkbox('Login')
    st.sidebar.write('Simply - Tick to Login | UnTick to Logout')
    
    if login:
        user = auth.sign_in_with_email_and_password(email,password)
        with st.spinner("Loading..."):
            #FROM FIREBASE
            user_handle = db.child(user['localId']).child("user_handle").get().val()
            name = db.child(user['localId']).child("name").get().val()
            country = db.child(user['localId']).child("country").get().val()

            #LOCAL FILES
            movie_dict = pickle.load(open('Recommendation\movie_dict.pkl','rb'))
            #new df is now here via the file - as dict
            movies = pd.DataFrame(movie_dict)
            similarity = pickle.load(open('Recommendation\similarity.pkl','rb'))
        

            #DISPLAY PART
            st.title('Welcome ' + name)
            st.write('UserID : '+ user_handle + " | Country: "+country)
            selected_movie_name = st.selectbox('Hey, It\'s so simple, just type out a movie name that you have seen or with respect to which you need to see the results, then click on \'Recommend Me\'  ',movies['title'].values)
            st.session_state['selected_movie_name'] = selected_movie_name
            st.session_state['button'] = True
            st.write('You selected:', st.session_state.get('selected_movie_name'))
            movie_index = movies[movies['title'] == selected_movie_name].index[0]
            sel_poster_url = fetch_poster(movies['movie_id'][movie_index])
            st.image(sel_poster_url,width=150)

            if st.checkbox('Recommend Me'):
                with st.spinner("Loading..."):
                    names,posters,genres = recommend(selected_movie_name,movies,similarity)
                    print(genres)
                    st.write("**Hooray! Here are the Top 5 Recommendations from our Recommendation Model:**")
                    col1, col2, col3, col4, col5 = st.columns(5)
                    with col1:
                        st.text("1. "+names[0])
                        st.image(posters[0])
                        st.text("Genre: "+genres[0])
                    with col2:
                        st.text("2. "+names[1])
                        st.image(posters[1])
                        st.text("Genre: "+genres[1])
                    with col3:
                        st.text("3. "+names[2])
                        st.image(posters[2])
                        st.text("Genre: "+genres[2])
                    with col4:
                        st.text("4. "+names[3])
                        st.image(posters[3])
                        st.text("Genre: "+genres[3])
                    with col5:
                        st.text("5. "+names[4])
                        st.image(posters[4])
                        st.text("Genre: "+genres[4])

        
        
                        
        
#Removing the made by 
hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True) 


