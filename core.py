import bypasser
import re
import freewall

def handle_index(ele):
    return bypasser.scrapeIndex(ele)

def loop_thread(url):
    urls = []
    urls.append(url)

    if not url:
        return None

    link = ""
    temp = None
    for ele in urls:
        if re.search(r"https?:\/\/(?:[\w.-]+)?\.\w+\/\d+:", ele):
            handle_index(ele)
        elif bypasser.ispresent(bypasser.ddl.ddllist, ele):
            try:
                temp = bypasser.ddl.direct_link_generator(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        elif freewall.pass_paywall(ele, check=True):
            freefile = freewall.pass_paywall(ele)
            if freefile:
                # Returning the filename/path if a file is downloaded
                return freefile
                # Note: original app.py returned send_file(freefile).
                # Here we return the path so the caller decides what to do.
        else:
            try:
                temp = bypasser.shortners(ele)
            except Exception as e:
                temp = "**Error**: " + str(e)
        print("bypassed:", temp)
        if temp:
            link = link + temp + "\n\n"

    return link
