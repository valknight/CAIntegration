import time
import json
import os
import sys
import click
import spotify
import requests

from config import PORT
from web import start_server
from config import get_spotify_config

queued_alerts = []
# Main code
uri = None
sp = None

def generate_spotify_code(uri):
    spotify_code_url = "https://scannables.scdn.co/uri/plain/{file_format}/{bg_color}/{color}/1280/{uri}"
    BG_COLOR, COLOR = get_spotify_config()
    formattedSvg = spotify_code_url.format(bg_color=BG_COLOR, color=COLOR, uri=uri, file_format="svg")
    formattedPng = spotify_code_url.format(bg_color=BG_COLOR, color=COLOR, uri=uri, file_format="png")
    rSvg = requests.get(formattedSvg)
    with open('web/spotify_code.svg', 'w') as f:
        f.write(rSvg.text)
    rPng = requests.get(formattedPng, stream=True)
    with open('web/spotify_code.png', 'wb') as f:
        rPng.raw.decode_content = True
        for chunk in rPng:
            f.write(chunk)
    return rSvg.text


def download_album_art(playback):
    top_image = playback['item']['album']['images'][0]['url']
    r = requests.get(top_image, stream=True)
    with open('web/album_art.png', 'wb') as f:
        r.raw.decode_content = True
        for chunk in r:
            f.write(chunk)


if __name__ == '__main__':
    try:
        # Check we're actually logged in as... me?
        click.echo("CustomAudioIntegration | github.com/valknight | twitch.tv/VKniLive")
        click.echo("Logging into Spotify...")
        click.echo("Your browser window may pop up!")
        sp = spotify.CAIntegrationSpotifyApiWrapper()
        click.echo("Hiya {}!".format(sp.user_info['display_name']))
        ws = start_server()
        if (ws):
            print("Your web source in OBS is: http://127.0.0.1:{}".format(PORT))
        else:
            click.echo(click.style("Oops! Your platform isn't quite supported for web. Start a web server at the 'web' directory though, and you should be good to go!", fg='red'))
        click.echo(click.style("Press CTRL-C to quit.", fg='black', bg='white'))
        while True:
            try:
                playback = sp.playback
                if type(playback) == dict:
                    if playback['is_playing']:
                        if playback['item']['uri'] != uri:
                            uri = playback['item']['uri']
                            # write track names for those using OBS
                            with open('web/track.txt', 'w') as f:
                                f.write(playback['item']['name'])
                            # write artist names for those using OBS
                            artists = []
                            for artist in playback['item']['artists']:
                                artists.append(artist['name'])
                            with open('web/artist.txt', 'w') as f:
                                f.write(', '.join(artists))
                            # download album art
                            download_album_art(playback)
                            # Get Spotify code
                            code = generate_spotify_code(playback['item']['uri'])
                            playback['scannable_code_svg'] = code
                            with open("web/song.json", "w") as f:
                                f.write(json.dumps(playback))
                else:
                    with open("web/song.json", "w") as f:
                        f.write(json.dumps(playback))
            except ConnectionError:
                pass
            except Exception as e:
                print("An unknown error occurred!")
                print(e)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down!")
        files = [
            "song.json",
            "album_art.png",
            "spotify_code.png",
            "spotify_code.svg",
            "artist.txt",
            "track.txt"
        ]
        for f in files:
            try:
                os.remove("web/{}".format(f))
                click.echo("cleaned up {}".format(f))
            except FileNotFoundError:
                click.echo("no need to cleanup {} - already deleted".format(f))
        click.echo("All done! Thanks for using CustomAudioIntegration")
        click.echo("o7 - val")
        click.pause("Press any key to quit.")
        sys.exit(0)