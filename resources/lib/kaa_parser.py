import requests
import simplejson as json
import re, hashlib, time, base64

def get_json(t):
   a = re.search(r"appData = (.+?) \|\|", t)
   if a:
      return json.loads(a.group(1))
   return {}

def get_main():
   req = requests.get("https://www.kickassanime.rs/")
   if req.status_code == 200:
      data = get_json(req.text)
      del data["notes"]
      del data["ax"]
      return data
   return {'response_code':req.status_code,'sig':"",'clip':"",'vt':"",'scheduleList':[],'animeList':{'all':[],'dub':[],'sub':[]}}

def search(keyword):
   data = get_main()
   keyword = keyword.strip()
   mt = str(int(time.time()))
   hashdata = keyword+mt+data["sig"]+data["clip"]+"sa"
   sig = hashlib.sha1(hashdata).hexdigest().upper()
   payload = {'keyword':keyword, 'mt':mt, 'ek':data["sig"], 'vt':data["vt"], 'sig':sig}
   req = requests.post("https://www.kickassanime.rs/api/anime_search", data=payload)
   if req.status_code == 200:
      return json.loads(req.text)
   return []

def get_schedule():
   data = get_main()
   return data["scheduleList"]

def get_new(page, subdub):
   data = get_main()
   if (page == 1):
      return data["animeList"][subdub]
   else:
      hashdata = data["sig"]+data["vt"]+data["clip"]+"gal"
      sig = hashlib.sha1(hashdata).hexdigest().upper()
      url = "https://www.kickassanime.rs/api/get_anime_list/{0}/{1}?hash={2}&vt={3}&sig={4}".format(subdub, page, data["sig"], data["vt"], sig)
      req = requests.get(url)
      if req.status_code == 200:
         return json.loads(req.text)["data"]
      return []

def get_anime(anime_slug):
   req = requests.get("https://www.kickassanime.rs/anime/{0}".format(anime_slug))
   if req.status_code == 200:
      return get_json(req.text)["anime"]
   return {}

def get_episode(anime_slug, episode_slug):
   req = requests.get("https://www.kickassanime.rs/anime/{0}/{1}".format(anime_slug, episode_slug))
   if req.status_code == 200:
      return get_json(req.text)
   return {}

def sort_key(elem):
   elem = elem[1]
   if "1080" in elem:
      return 1
   elif "720" in elem:
      return 2
   elif "480" in elem:
      return 3
   elif "360" in elem:
      return 4
   elif "144" in elem:
      return 5
   else:
      return 6

def get_premium_links(episode_object):
   fin_links = []
   keys = [ln for ln in episode_object.keys() if ln.startswith("link")]
   for k in keys:
      if episode_object[k].startswith("https://haloani.ru/mobile2/"):
         req = requests.get(episode_object[k])
         if req.status_code == 200:
            sites = re.findall(r"<option value=\"(.+?)\">(.+?)</option>", req.text)
            for site in sites:
               req = requests.get(site[0])
               if req.status_code == 200:
                  match = re.search("document.write\\((?:Base64.decode|atob)\\((?:\"|')(.+?)(?:\"|')\\)\\)", req.text)
                  if match:
                     match = " ".join(str(base64.standard_b64decode(match.group(1)+"============")).split("\n"))
                  else:
                     match = " ".join(req.text.split("\n"))
                  links = re.findall(r"<a rel=\"?nofollow\"? target=\"?_blank\"? href=\"(.+?)\".+?>(.+?)</a>", match)
                  for link in links:
                     req = requests.head(link[0])
                     lo = link[0]
                     if req.status_code == 302:
                        lo = req.headers["Location"]
                     fin_links.append((lo, link[1].split(">")[-1].replace("Original", "").strip(), site[1]))
   fin = sorted(fin_links, key=sort_key)
   return fin


def scrape_player(episode_object):
   # I probably need to use something like openscrapers to get this working without having to
   # do a rediculous ammount of reverse engineering myself
   # no idea how to do that, so v1.0 doesn't need it
   pass
