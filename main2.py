import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import Counter
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import numpy as np

load_dotenv()

st.set_page_config(layout="wide")
st.title('Advanced Spotify User Analysis Dashboard')

if 'token_info' not in st.session_state:
    st.session_state.token_info = None

SCOPE = (
    "user-read-private "
    "user-read-email "
    "user-read-recently-played "
    "user-top-read "
    "user-library-read "
    "user-follow-read "
    "playlist-read-private "
    "user-read-currently-playing "
    "user-read-playback-state"
)

sp_oauth = SpotifyOAuth(
    client_id=os.getenv('CLIENT_ID'),
    client_secret=os.getenv('CLIENT_SECRET'),
    redirect_uri='http://localhost:8501',
    scope=SCOPE,
    cache_path=None
)

if not st.session_state.token_info:
    auth_url = sp_oauth.get_authorize_url()
    st.write("Welcome! Please login to your Spotify account:")
    st.markdown(f"[Login to Spotify]({auth_url})")
    
    if 'code' in st.query_params:
        code = st.query_params['code']
        token_info = sp_oauth.get_access_token(code)
        st.session_state.token_info = token_info
        st.rerun()

if st.session_state.token_info:
    try:
        sp = spotipy.Spotify(auth=st.session_state.token_info['access_token'])
        
        # Get user profile
        user = sp.current_user()
        st.sidebar.title(f"Welcome {user.get('display_name', 'User')}!")
        
        # Create tabs
        tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
            "Music Taste Evolution",
            "Playlist Analysis",
            "Library Statistics",
            "Genre Analysis",
            "Current Trends",
            "Other Tracks You Might Like",
            "ML Analysis"
        ])
        
        # Tab 1: Music Taste Evolution
        with tab1:
            st.header("Evolution of Music Taste")
            
            periods = {
                'Last 4 Weeks': 'short_term',
                'Last 6 Months': 'medium_term',
                'All Time': 'long_term'
            }
            
            for period_name, period in periods.items():
                st.subheader(period_name)
                
                try:
                    top_tracks = sp.current_user_top_tracks(limit=20, time_range=period)
                    
                    if top_tracks and top_tracks['items']:
                        tracks_data = []
                        for track in top_tracks['items']:
                            tracks_data.append({
                                'Track Name': track['name'],
                                'Artist': track['artists'][0]['name'],
                                'Popularity': track['popularity']
                            })
                        
                        if tracks_data:
                            df = pd.DataFrame(tracks_data)
                            st.dataframe(df)
                            
                            fig = px.bar(df, 
                                      x='Track Name',
                                      y='Popularity',
                                      hover_data=['Artist'],
                                      title=f'Track Popularity - {period_name}')
                            fig.update_layout(xaxis={'tickangle': 45})
                            st.plotly_chart(fig)
                    else:
                        st.warning(f"No top tracks found for {period_name}")
                except Exception as e:
                    st.error(f"Error getting top tracks for {period_name}: {str(e)}")
        
        # Tab 2: Playlist Analysis
        with tab2:
            st.header("Playlist Analysis")
            
            try:
                playlists = sp.current_user_playlists()
                if playlists and playlists['items']:
                    playlist_data = []
                    
                    for playlist in playlists['items']:
                        playlist_data.append({
                            'Name': playlist['name'],
                            'Tracks': playlist['tracks']['total'],
                            'Public': playlist['public'],
                            'Collaborative': playlist['collaborative']
                        })
                    
                    if playlist_data:
                        df_playlists = pd.DataFrame(playlist_data)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Total Playlists", len(playlist_data))
                            fig = px.bar(df_playlists, 
                                       x='Name', 
                                       y='Tracks',
                                       title='Tracks per Playlist')
                            fig.update_layout(xaxis={'tickangle': 45})
                            st.plotly_chart(fig)
                        
                        with col2:
                            st.metric("Total Tracks", df_playlists['Tracks'].sum())
                            public_counts = df_playlists['Public'].value_counts()
                            fig = px.pie(values=public_counts.values,
                                       names=['Private', 'Public'],
                                       title='Playlist Visibility')
                            st.plotly_chart(fig)
                    else:
                        st.warning("No playlist data available")
                else:
                    st.warning("No playlists found")
            except Exception as e:
                st.error(f"Error analyzing playlists: {str(e)}")
        
        # Tab 3: Library Statistics
        with tab3:
            st.header("Library Statistics")
            
            try:
                saved_tracks = sp.current_user_saved_tracks(limit=50)
                saved_albums = sp.current_user_saved_albums(limit=50)
                
                if saved_tracks and saved_albums:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Saved Tracks", saved_tracks['total'])
                        st.metric("Saved Albums", saved_albums['total'])
                    
                    # Create timeline of saved tracks
                    if saved_tracks['items']:
                        saved_data = []
                        for item in saved_tracks['items']:
                            try:
                                # Handle both datetime formats
                                date_str = item['added_at']
                                if '.' in date_str:  # Contains milliseconds
                                    added_at = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S.%fZ')
                                else:  # Without milliseconds
                                    added_at = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%SZ')
                                    
                                saved_data.append({
                                    'Track': item['track']['name'],
                                    'Added At': added_at
                                })
                            except Exception as date_error:
                                st.warning(f"Couldn't parse date for track: {item['track']['name']}")
                                continue
                        
                        if saved_data:
                            df_saved = pd.DataFrame(saved_data)
                            fig = px.histogram(df_saved, 
                                            x='Added At',
                                            title='When You Save Tracks')
                            st.plotly_chart(fig)
                        else:
                            st.warning("No timeline data available")
                else:
                    st.warning("No library data available")
            except Exception as e:
                st.error(f"Error analyzing library: {str(e)}")
                
        # Tab 4: Genre Analysis
        with tab4:   #Add for short and medium term too
            st.header("Genre Analysis")
            
            try:
                top_artists = sp.current_user_top_artists(limit=10, time_range='long_term')
                if top_artists and top_artists['items']:
                    genres = []
                    for artist in top_artists['items']:
                        genres.extend(artist['genres'])
                    
                    if genres:
                        genre_counts = Counter(genres)
                        fig = px.pie(values=list(genre_counts.values()),
                                   names=list(genre_counts.keys()),
                                   title='Your Music Genres')
                        st.plotly_chart(fig)
                    else:
                        st.warning("No genre data available")
                else:
                    st.warning("No top artists found")
            except Exception as e:
                st.error(f"Error analyzing genres: {str(e)}")
        
        # Tab 5: Current Trends
        with tab5:
            st.header("Current Trends")
            
            try:
                recent = sp.current_user_recently_played(limit=50)
                if recent and recent['items']:
                    recent_data = []
                    for item in recent['items']:
                        played_at = datetime.strptime(item['played_at'], '%Y-%m-%dT%H:%M:%S.%fZ')
                        recent_data.append({
                            'Track': item['track']['name'],
                            'Artist': item['track']['artists'][0]['name'],
                            'Played At': played_at,
                            'Hour': played_at.hour,
                            'Day': played_at.strftime('%A')
                        })
                    
                    if recent_data:
                        df_recent = pd.DataFrame(recent_data)
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            fig = px.histogram(df_recent, 
                                             x='Hour',
                                             title='Listening Activity by Hour')
                            st.plotly_chart(fig)
                        
                        with col2:
                            day_counts = df_recent['Day'].value_counts()
                            fig = px.pie(values=day_counts.values,
                                       names=day_counts.index,
                                       title='Listening Activity by Day')
                            st.plotly_chart(fig)
                        
                        st.subheader("Recently Played")
                        st.dataframe(df_recent[['Track', 'Artist', 'Played At']].head(10))
                    else:
                        st.warning("No recent listening data available")
                else:
                    st.warning("No recently played tracks found")
            except Exception as e:
                st.error(f"Error analyzing recent tracks: {str(e)}")
        

        with tab6:
            # Add this as a new tab or section
            st.header("Popular Tracks from Your Favorite Artists")

            try:
                # First, let's verify we're getting top artists
                top_artists = sp.current_user_top_artists(limit=5, time_range='long_term')
                
                # Debug print
                st.write("Number of top artists found:", len(top_artists['items']) if top_artists and 'items' in top_artists else 0)
                
                if top_artists and top_artists['items']:
                    for artist in top_artists['items']:
                        st.write(f"Processing artist: {artist['name']}")  # Debug print
                        
                        # Get this artist's top tracks (specify market)
                        artist_top_tracks = sp.artist_top_tracks(artist['id'], country=user['country'])
                        
                        # Debug print
                        st.write(f"Number of top tracks found for {artist['name']}:", 
                                len(artist_top_tracks['tracks']) if artist_top_tracks and 'tracks' in artist_top_tracks else 0)
                        
                        if artist_top_tracks and 'tracks' in artist_top_tracks:
                            tracks_data = []
                            for track in artist_top_tracks['tracks'][:5]:  # Limit to top 5 tracks
                                tracks_data.append({
                                    'Track Name': track['name'],
                                    'Popularity': track['popularity'],
                                    'Album': track['album']['name'],
                                    'Preview URL': track['preview_url']
                                })
                            
                            if tracks_data:
                                df = pd.DataFrame(tracks_data)
                                st.write(f"### Top Tracks by {artist['name']}")
                                
                                # Display tracks table
                                st.dataframe(df[['Track Name', 'Popularity', 'Album']])
                                
                                # Create popularity chart
                                fig = px.bar(df, 
                                            x='Track Name',
                                            y='Popularity',
                                            title=f'Popular Tracks - {artist["name"]}')
                                fig.update_layout(xaxis={'tickangle': 45})
                                st.plotly_chart(fig)
                                
                                # Add preview links if available
                                st.write("Preview Links:")
                                for idx, track in enumerate(tracks_data):
                                    if track['Preview URL']:
                                        st.audio(track['Preview URL'])
                else:
                    st.warning("No top artists found. Try listening to more music to generate this data.")

            except Exception as e:
                st.error(f"Error in artist analysis: {str(e)}")
                st.write("Debug info:", str(e))  # More detailed error info

        with tab7:
            st.header("Machine Learning Insights")
            
            try:
                # Get recent and top tracks for analysis
                recent_tracks = sp.current_user_recently_played(limit=20)
                top_tracks = sp.current_user_top_tracks(limit=20)
                
                # Combine tracks
                all_tracks = []
                
                # Add recent tracks
                if recent_tracks and recent_tracks['items']:
                    for item in recent_tracks['items']:
                        track = item['track']
                        # Get artist genres
                        artist = sp.artist(track['artists'][0]['id'])
                        genres = artist['genres'] if artist['genres'] else []
                        
                        all_tracks.append({
                            'name': track['name'],
                            'artist': track['artists'][0]['name'],
                            'popularity': track['popularity'],
                            'duration_ms': track['duration_ms'],
                            'explicit': 1 if track['explicit'] else 0,
                            'genres': genres,
                            'type': 'Recent'
                        })
                
                # Add top tracks
                if top_tracks and top_tracks['items']:
                    for track in top_tracks['items']:
                        # Get artist genres
                        artist = sp.artist(track['artists'][0]['id'])
                        genres = artist['genres'] if artist['genres'] else []
                        
                        all_tracks.append({
                            'name': track['name'],
                            'artist': track['artists'][0]['name'],
                            'popularity': track['popularity'],
                            'duration_ms': track['duration_ms'],
                            'explicit': 1 if track['explicit'] else 0,
                            'genres': genres,
                            'type': 'Top'
                        })
                
                if all_tracks:
                    df = pd.DataFrame(all_tracks)
                    
                    # Create genre features (one-hot encoding)
                    all_genres = set()
                    for genres in df['genres']:
                        all_genres.update(genres)
                    
                    # Create genre columns
                    for genre in all_genres:
                        df[f'genre_{genre}'] = df['genres'].apply(lambda x: 1 if genre in x else 0)
                    
                    # Prepare features for clustering
                    numerical_features = ['popularity', 'duration_ms', 'explicit']
                    genre_features = [col for col in df.columns if col.startswith('genre_')]
                    features = numerical_features + genre_features
                    
                    X = df[features].values
                    
                    # Scale the features
                    scaler = StandardScaler()
                    X_scaled = scaler.fit_transform(X)
                    
                    # Perform clustering
                    kmeans = KMeans(n_clusters=5, random_state=42)
                    clusters = kmeans.fit_predict(X_scaled)
                    df['Cluster'] = clusters
                    
                    # Display clusters
                    st.subheader("Song Clusters Analysis (Including Genres)")
                    
                    # Scatter plot of clusters
                    fig = px.scatter(df, 
                                x='popularity', 
                                y='duration_ms',
                                color='Cluster',
                                hover_data=['name', 'artist'],
                                title='Song Clusters based on Features and Genres')
                    st.plotly_chart(fig)
                    
                    # Analysis of each cluster
                    for cluster in range(5):
                        cluster_tracks = df[df['Cluster'] == cluster]
                        st.write(f"### Cluster {cluster + 1} Characteristics:")
                        
                        # Basic metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Average Popularity", 
                                    f"{cluster_tracks['popularity'].mean():.1f}")
                        with col2:
                            st.metric("Average Duration", 
                                    f"{(cluster_tracks['duration_ms'].mean() / 60000):.2f} min")
                        with col3:
                            st.metric("Explicit Content",
                                    f"{(cluster_tracks['explicit'].mean() * 100):.1f}%")
                        
                        # Most common genres in this cluster
                        cluster_genres = []
                        for _, row in cluster_tracks.iterrows():
                            cluster_genres.extend(row['genres'])
                        
                        if cluster_genres:
                            genre_counts = Counter(cluster_genres)
                            st.write("Top genres in this cluster:")
                            for genre, count in genre_counts.most_common(5):
                                st.write(f"- {genre}: {count} tracks")
                        
                        st.write("Sample tracks from this cluster:")
                        st.dataframe(cluster_tracks[['name', 'artist', 'type']].head())
                        st.write("---")
                    
                    # Genre distribution visualization
                    st.subheader("Genre Distribution Across Clusters")
                    genre_cluster_data = []
                    for cluster in range(5):
                        cluster_tracks = df[df['Cluster'] == cluster]
                        cluster_genres = []
                        for _, row in cluster_tracks.iterrows():
                            cluster_genres.extend(row['genres'])
                        
                        genre_counts = Counter(cluster_genres)
                        for genre, count in genre_counts.most_common(5):
                            genre_cluster_data.append({
                                'Cluster': f'Cluster {cluster + 1}',
                                'Genre': genre,
                                'Count': count
                            })
                    
                    genre_df = pd.DataFrame(genre_cluster_data)
                    fig = px.bar(genre_df, 
                                x='Cluster',
                                y='Count',
                                color='Genre',
                                title='Top Genres by Cluster')
                    st.plotly_chart(fig)
                    
                else:
                    st.warning("Not enough track data for analysis")
                    
            except Exception as e:
                st.error(f"Error in ML analysis: {str(e)}")
                st.write("Debug info:", str(e))

        if st.sidebar.button('Logout'):
            st.session_state.token_info = None
            st.rerun()

            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.session_state.token_info = None