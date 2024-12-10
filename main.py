from dotenv import load_dotenv
import os
import base64
from requests import post, get
import json
import pandas as pd
import streamlit as st


# Load environment variables
load_dotenv()

# Get environment variable from Streamlit secrets or fallback to os.environ (we actually don't need since secrets.toml exists)
def get_env(secret):
    try:
        return st.secrets[secret]
    except:
        return os.getenv(secret)
    
# Get credentials from environment variables
client_id = get_env("CLIENT_ID")
client_secret = get_env("CLIENT_SECRET")
redirect_uri = get_env("REDIRECT_URI")

def get_token():
    auth_string = client_id + ":" + client_secret
    auth_bytes = auth_string.encode('utf-8')
    auth_base64 = str(base64.b64encode(auth_bytes), 'utf-8')
    
    url = "https://accounts.spotify.com/api/token"
    headers = {
        "Authorization": "Basic " + auth_base64,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    data = {"grant_type": "client_credentials"}
    
    result = post(url, headers=headers, data=data)
    json_result = json.loads(result.content)
    token = json_result["access_token"]
    return token

def get_auth_header(token):
    return {"Authorization": "Bearer " + token}

def search_for_artist(artist_name, token):
    url = "https://api.spotify.com/v1/search"
    headers = get_auth_header(token)
    query = f'q={artist_name}&type=artist&limit=1'
    
    query_url = url + "?" + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["artists"]["items"]
    
    return json_result

def get_songs_by_artist(artist_id, token):
    url = f"https://api.spotify.com/v1/artists/{artist_id}/top-tracks"
    headers = get_auth_header(token)
    query = "market=US"
    
    query_url = url + "?" + query
    result = get(query_url, headers=headers)
    json_result = json.loads(result.content)["tracks"]
    
    return json_result
 


def main():
    st.title("Spotify Artist Search")
    
    artist_name = st.text_input("Enter artist name:")
    
    if artist_name:
        token = get_token()
        result = search_for_artist(artist_name, token)   #result is a list of dictionaries of artist with artist_name
        top_artist=result[0]
        
        df = pd.DataFrame([{
            'Name': top_artist['name'],
            'Popularity': top_artist['popularity'],
            'Followers': top_artist['followers']['total'],
            'Genres': ', '.join(top_artist['genres'])
        }])
        
        st.dataframe(df)
    
        st.write("Top tracks:")
        artist_id = top_artist["id"]
        top_tracks = get_songs_by_artist(artist_id, token)
        
        df = pd.DataFrame([{
            'Name': track['name'],
            'Popularity': track['popularity'],
            'Duration': track['duration_ms'] / 1000
        } for track in top_tracks])
        
        st.dataframe(df)


   

main()