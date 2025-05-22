import os
import time
import requests
import base64
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# La Cuerda

def fetch_all_artists(estilo_id: str, increment: int = 50, max_retries: int = 3, delay: int = 1) -> list[str]:
    """
    Iteratively fetch artist URLs by incrementing the 'ini' parameter.

    Parameters:
    - base_url (str): The base URL with placeholders for 'ini'.
    - increment (int): The amount to increment 'ini' each time.
    - max_retries (int): Number of retries for failed requests.
    - delay (int or float): Seconds to wait between requests.

    Returns:
    - List of all artist URLs.
    """
    all_artists = []
    ini = 0
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/1.0; +https://yourdomain.com/bot)"
    }

    while True:
        # Construct the URL with the current 'ini' value
        params = {
            "ini": ini,
            "req_pais": "ar",
            "req_estilo": estilo_id
        }
        url = f"https://acordes.lacuerda.net/ARCH/indices.php"

        try:
            resp = session.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to fetch page with ini={ini}. Error: {e}")
            break  # Stop on request failure

        soup = BeautifulSoup(resp.text, "html.parser")

        main_ul = soup.find("ul", id="i_main")
        if not main_ul:
            print(f"No artist list found on page with ini={ini}. Stopping.")
            break  # No more artists to fetch

        # Extract artist links from the current page
        artist_links = []
        for li in main_ul.find_all("li"):
            a_tag = li.find("a")
            if a_tag and a_tag.has_attr("href"):
                relative_link = a_tag["href"].strip()
                full_url = urljoin("https://acordes.lacuerda.net", relative_link)
                artist_links.append(full_url)

        if not artist_links:
            print(f"No artists found on page with ini={ini}. Stopping.")
            break  # No artists found; assume no more pages

        print(f"Fetched {len(artist_links)} artists from ini={ini}.")

        all_artists.extend(artist_links)

        ini += increment
        time.sleep(delay)

    return all_artists

def extract_urls_from_page(page_url: str) -> list[str]:
    """
    Fetches the HTML content from the given URL and extracts a list of absolute URLs
    from the <ul> element with id 'b_main'.

    Args:
        page_url (str): The URL of the webpage to extract URLs from.

    Returns:
        list: A list of absolute URLs extracted from the page.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) ' +
                      'AppleWebKit/537.36 (KHTML, like Gecko) ' +
                      'Chrome/58.0.3029.110 Safari/537.3'
    }

    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4XX, 5XX)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    urls = []

    # Find the <ul> element with id 'b_main'
    b_main = soup.find('ul', id='b_main')
    if not b_main:
        print("No <ul> with id 'b_main' found.")
        return urls

    # Find all <a> tags within this <ul>
    a_tags = b_main.find_all('a', href=True)
    if not a_tags:
        print("No <a> tags with href found within <ul id='b_main'>.")
        return urls

    for a in a_tags:
        href = a['href'].strip()
        # Construct the full URL
        full_url = urljoin(page_url, href)
        urls.append(full_url)

    return urls

def extract_lyrics_from_url(page_url: str) -> str:
    """
    Fetches the HTML content from the given URL and extracts the lyrics
    contained within the <div class="rLetra"> element.

    Args:
        page_url (str): The URL of the webpage to extract lyrics from.

    Returns:
        str: The extracted lyrics as a clean string. Returns an empty string
             if lyrics are not found or an error occurs.
    """
    headers = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/58.0.3029.110 Safari/537.3'
        )
    }

    try:
        response = requests.get(page_url, headers=headers, timeout=10)
        response.raise_for_status()  # Raise HTTPError for bad responses (4XX, 5XX)
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the URL: {e}")
        return ""

    soup = BeautifulSoup(response.text, 'html.parser')

    # Find the <div> with class 'rLetra'
    r_letra_div = soup.find('div', class_='rLetra')
    if not r_letra_div:
        print("No <div> with class 'rLetra' found.")
        return ""

    lyrics = r_letra_div.get_text(separator='<br>', strip=True)

    return lyrics

# Spotify
# Para ejecutar la función se necesita tener acceso a la api de Spotify:
# https://developer.spotify.com/documentation/web-api

client_id = os.getenv("SPOTIFY_CLIENT_ID")
client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")

def search_spotify(song: str, artist: str, client_id: str = client_id, client_secret: str = client_secret) -> dict:
    """
    Search for a specific track on Spotify using the Spotify Web API.

    Parameters:
        song (str): The title of the song to search for.
        artist (str): The name of the artist associated with the song.
        client_id (str, optional): Spotify API client ID. Defaults to global `client_id`.
        client_secret (str, optional): Spotify API client secret. Defaults to global `client_secret`.

    Returns:
        dict: A dictionary containing the track name, album name, release date, 
              and full metadata of the matched track if found. 
              Returns an empty dictionary if no match is found or if an error occurs.
    
    Raises:
        RuntimeError: If authentication with Spotify fails.
    """
    auth_url = 'https://accounts.spotify.com/api/token'

    auth_headers = {
        'Authorization': 'Basic ' + base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    }
    auth_data = {
        'grant_type': 'client_credentials'
    }

    auth_response = requests.post(auth_url, headers=auth_headers, data=auth_data)

    if auth_response.status_code == 200:
        access_token = auth_response.json()['access_token']
    else:
        print(f"Error de autenticación: {auth_response.status_code}")
        raise(RuntimeError)

    search_url = 'https://api.spotify.com/v1/search'
    search_headers = {
        'Authorization': f'Bearer {access_token}'
    }
    search_params = {
        'q': f'track:{song} artist:{artist}',
        'type': 'track',
        'limit': 1
    }

    search_response = requests.get(search_url, headers=search_headers, params=search_params)

    if search_response.status_code == 200:
        data = search_response.json()
        tracks = data.get('tracks', {}).get('items', [])
        if tracks:
            track = tracks[0]
            name = track['name']
            album = track['album']['name']
            release_date = track['album']['release_date']
            return {"track":name, "album":album, "release_date": release_date, "metadata":tracks}
        else:
            print("No data found for", song, artist)
            return {}
    else:
        return {}



