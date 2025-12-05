from flask import Flask, request, render_template, make_response, send_file
import bypasser
import re
import os
import freewall
import core


app = Flask(__name__)


def store_shortened_links(link):
    with open('shortened_links.txt', 'a') as file:
        file.write(link + '\n')


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        url = request.form.get("url")
        result = core.loop_thread(url)
        if freewall.pass_paywall(url, check=True):
            try: return send_file(result)
            except: return result
        
        shortened_links = request.cookies.get('shortened_links')
        if shortened_links:
            prev_links = shortened_links.split(',')
        else:
            prev_links = []

        if result:
            prev_links.append(result)
           
            if len(prev_links) > 10: 
                prev_links = prev_links[-10:]  

        shortened_links_str = ','.join(prev_links)        
        resp = make_response(render_template("index.html", result=result, prev_links=prev_links))
        resp.set_cookie('shortened_links', shortened_links_str)

        return resp

    shortened_links = request.cookies.get('shortened_links')
    return render_template("index.html", result=None, prev_links=shortened_links.split(",") if shortened_links else None)



if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
