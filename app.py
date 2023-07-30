from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
import os
from urllib.parse import urlparse

app = Flask(__name__, template_folder=os.path.join(os.path.dirname(__file__), 'templates'))

def get_search_url(search_engine, query):
    if search_engine == "google.de" or search_engine == "google.com":
        url = f"https://www.{search_engine}/search?q={query}"
    elif search_engine == "bing.de" or search_engine == "bing.com":
        url = f"https://www.{search_engine}/search?q={query}"
    return url

def get_rank(url, domain, search_engine):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
    }
    try:
        max_pages = 10  # Maximum number of pages to check (up to 100 results)
        current_page = 0

        while current_page < max_pages:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            rank = -1

            if search_engine.startswith("google"):
                search_results = soup.find_all("div", class_="tF2Cxc")
                for index, result in enumerate(search_results):
                    link = result.find("a")["href"]
                    parsed_url = urlparse(link)
                    if domain in parsed_url.hostname:
                        rank = index + 1
                        break

            elif search_engine.startswith("bing"):
                search_results = soup.find_all("li", class_="b_algo")
                for index, result in enumerate(search_results):
                    link = result.find("a")["href"]
                    parsed_url = urlparse(link)
                    if domain in parsed_url.hostname:
                        rank = index + 1
                        break

            if rank != -1:
                return rank

            next_page_link = soup.find("a", id="pnnext")
            if next_page_link:
                url = "https://www.google.com" + next_page_link["href"]
            else:
                break

            current_page += 1

        return rank

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        return None, error_msg

    except requests.exceptions.RequestException as e:
        error_msg = str(e)
        return None, error_msg


def main(domain, search_engine, keywords):
    keyword_results = []

    for keyword in keywords:
        query = keyword.strip().replace(" ", "+")
        search_url = get_search_url(search_engine, query)
        rank = get_rank(search_url, domain, search_engine)

        # Fetch search results for each keyword
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        }
        response = requests.get(search_url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        search_results = []
        if search_engine.startswith("google"):
            results = soup.find_all("div", class_="tF2Cxc")
            for index, result in enumerate(results):
                link = result.find("a")["href"]
                title = result.find("h3").get_text()
                snippet_element = result.find("div", class_="IsZvec")
                snippet = snippet_element.get_text() if snippet_element else ""
                search_results.append({
                    'rank': index + 1,
                    'title': title,
                    'link': link,
                    'snippet': snippet
                })

        elif search_engine.startswith("bing"):
            results = soup.find_all("li", class_="b_algo")
            for index, result in enumerate(results):
                link = result.find("a")["href"]
                title = result.find("h2").get_text()
                snippet_element = result.find("p")
                snippet = snippet_element.get_text() if snippet_element else ""
                search_results.append({
                    'rank': index + 1,
                    'title': title,
                    'link': link,
                   'snippet': snippet
                })

        keyword_results.append({
            'keyword': keyword,
            'rank': rank,
            'search_results': search_results
        })

    return keyword_results

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        domain = request.form['domain']
        search_engine = request.form['search_engine']
        keywords = request.form['keywords'].split(',')

        results = main(domain, search_engine, keywords)

       # with open("keyword_rankings.txt", "w") as file:
        #    for item in results:
        #        file.write(f"{item}\n")

        return render_template('result.html', results=results)
    else:
        return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)
