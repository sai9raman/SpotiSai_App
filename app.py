### ~~~~~~~~~~~~~~~~~~~ Imports ~~~~~~~~~~~~~~~~~~~ ###

from flask import Flask, request, url_for, redirect, render_template, jsonify
import os 

import pandas as pd
import numpy as np

from xgboost import XGBClassifier

import spotipy 
from spotipy.oauth2 import SpotifyClientCredentials


### ~~~~~~~~~~~~~~~~~~~ Config and setup ~~~~~~~~~~~~~~~~~~~ ###

client_id = os.environ['SPOTIFY_CID']
client_secret = os.environ['SPOTIFY_CS']
auth = SpotifyClientCredentials(client_id = client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=auth)



### ~~~~~~~~~~~~~~~~~~~ Core Functions ~~~~~~~~~~~~~~~~~~~ ###

def song_search(song_name, album_name):

    result = sp.search(q='album:'+album_name+' track:'+song_name,type='track')
    
    if result['tracks']['items'] == []:
        return {"Track Not Found": "No such tracks found"}
    
    return result['tracks']['items'][0]

def get_song_search_result(song_name, album_name):
    
    res = song_search(song_name, album_name)
    
    if "Track Not Found" in  res:
        return res 
    
    res_dict = {'Album': res['album']['name'], 
                'Artist': res['album']['artists'][0]['name'],
                'Track': res['name'],
                'Released': res['album']['release_date']
               } 
    
    return res_dict

### ~~~~~~~~~~~~~~~~~~ ###

def get_features(song_name, album_name):
    
    res = song_search(song_name, album_name)
    
    if "Track Not Found" in  res:
        return pd.DataFrame(res,index=[0]) 
    
    df = pd.DataFrame(index=[res['id']])
    
    af = sp.audio_features(res['id'])
    af = af[0]
    df['danergy'] = (af['danceability']+af['energy'])/2
    df['acousticness'] = af['acousticness']
    df['instrumentalness'] = af['instrumentalness']
    df['valence'] = af['valence']
    df['loudness'] = af['loudness']
    df['tempo'] = af['tempo']
    df['duration_secs'] = af['duration_ms']/1000

    return df

### ~~~~~~~~~~~~~~~~~~ ###

def xgb_prediction(df):
    
    if "Track Not Found" in df.columns:
        return "Track Not Found"
    
    xgb_model = XGBClassifier()
    xgb_model.load_model('SpotiSai.json')

    prediction = xgb_model.predict(df)[0]
    
    if prediction:
        return "Looks like Sai might like this song, you should go ahead and suggest this to him"
    else:        
        return "Hmm... this doesn't seem like a song he would like. But feel free to suggest this to him and check out" 
    

### ~~~~~~~~~~~~~~~~~~~ Flask App ~~~~~~~~~~~~~~~~~~~ ###


app = Flask(__name__)

@app.route("/")
@app.route("/home")
def home():

	return render_template('home.html')

@app.route('/search',methods=['POST'])
def search():

	song_name = request.form.get('song_name')
	album_name = request.form.get('album_name')

	res = get_song_search_result(song_name,album_name)
	
	if "Track Not Found" in  res:
		return render_template('home.html',res=res)

	prediction_str = xgb_prediction(get_features(song_name, album_name))

	res_str = ' '+str(res).replace('{','').replace('}','').replace("'",'').replace(',','<br>')
	return render_template('home.html',res=res,pred=prediction_str)


if __name__ == '__main__':
	app.run(debug=True)
