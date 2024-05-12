from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin

app = Flask(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:71.0) Gecko/20100101 Firefox/72.0"

def get_absolute_url(base_url, relative_url):
    return urljoin(base_url, relative_url)

def process_content(content, base_url):
    soup = BeautifulSoup(content, 'html.parser')
    base_tag = soup.new_tag('base', href=base_url)
    soup.head.insert(0, base_tag)

    for tag in soup.find_all(['a', 'img', 'script'], href=True, src=True):
        if 'href' in tag.attrs:
            tag['href'] = get_absolute_url(base_url, tag['href'])
        if 'src' in tag.attrs:
            tag['src'] = get_absolute_url(base_url, tag['src'])

    # Agregar script para abrir enlaces dentro del proxy
    script = soup.new_tag('script')
    script.string = """
        document.addEventListener('click', function(e) {
            var target = e.target;
            while (target && target.tagName !== 'A') {
                target = target.parentNode;
            }
            if (target) {
                e.preventDefault();
                fetch('/proxy', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: 'url=' + encodeURIComponent(target.href),
                }).then(function(response) {
                    return response.text();
                }).then(function(data) {
                    document.getElementById('content').innerHTML = data;
                });
            }
        });
    """
    soup.body.append(script)

    return str(soup)

def proxy_request(url):
    headers = {'User-Agent': USER_AGENT}
    response = requests.get(url, headers=headers)
    return response.content

@app.route('/')
def index():
    return render_template('index.html', content="")

@app.route('/proxy', methods=['POST'])
def proxy():
    url = request.form['url']

    try:
        # Obtener contenido de la URL a través del proxy
        web_content = proxy_request(url)
        web_content = process_content(web_content, url)
    except Exception as e:
        web_content = f"Error al obtener contenido: {str(e)}"

    return web_content

if __name__ == '__main__':
    app.run(debug=True)
