# -*- coding: utf-8 -*-

import routing
import logging
import xbmcaddon
from resources.lib import kodiutils
from resources.lib import kodilogging
from resources.lib import kaa_parser as kaa
from xbmc import translatePath
from xbmcgui import ListItem, Dialog, INPUT_ALPHANUM
from xbmcplugin import addDirectoryItem, endOfDirectory
from os import path, mkdir, remove

ADDON = xbmcaddon.Addon()
logger = logging.getLogger(ADDON.getAddonInfo('id'))
kodilogging.config()
plugin = routing.Plugin()
PROFILE = translatePath(ADDON.getAddonInfo('profile')).decode("utf-8")
if not path.exists(PROFILE):
    mkdir(PROFILE)

#-- main --#
@plugin.route('/')
def index():
    addDirectoryItem(plugin.handle, plugin.url_for(show_schedule), ListItem("Schedule"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(new_select), ListItem("New"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(new_search), ListItem("Search"), True)
    endOfDirectory(plugin.handle)

#-- schedule --#
@plugin.route('/schedule')
def show_schedule():
    for day in kaa.get_schedule():
        addDirectoryItem(plugin.handle, "", ListItem("---- {0} ----".format(day["day"].center(16))))
        for item in day["data"]:
            li = ListItem("({1}) - {0}".format(item["title"], item["time"]))
            li.setArt({'poster':"https://www.kickassanime.rs/uploads/{0}".format(item["image"])})
            addDirectoryItem(plugin.handle, plugin.url_for(show_anime, item["slug"][7:]), li, True)
    endOfDirectory(plugin.handle)

#--   new    --#
@plugin.route('/new')
def new_select():
    addDirectoryItem(plugin.handle, plugin.url_for(show_new, "all", 0), ListItem("All"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(show_new, "dub", 0), ListItem("Dubbed"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(show_new, "sub", 0), ListItem("Subbed"), True)
    endOfDirectory(plugin.handle)

@plugin.route('/new/<dubsub>/<page>')
def show_new(dubsub, page):
    page = int(page)
    init = False
    if page == 0:
        page = 1
        init = True
    if page > 1:
       addDirectoryItem(plugin.handle, plugin.url_for(show_new, dubsub, page-1), ListItem("[B]Prev Page[/B]"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(show_new, dubsub, page+1), ListItem("[B]Next Page[/B]"), True)
    items = kaa.get_new(page, dubsub)
    for item in items:
        li = ListItem("({0}) - {1} - [LIGHT]Ep {2}[/LIGHT]".format(item["type"], item["name"].replace("(Dub)", "").encode('ascii', errors='replace'), item["episode"]))
        li.setArt({'poster':"https://www.kickassanime.rs/uploads/{0}".format(item["poster"])})
        slug = item["slug"].split("/")
        addDirectoryItem(plugin.handle, plugin.url_for(show_episode, slug[1], slug[2]), li, True)
    if init:
        endOfDirectory(plugin.handle)
    else:
        endOfDirectory(plugin.handle, updateListing=True)
        

#--  search  --#
@plugin.route('/search')
def new_search():
    addDirectoryItem(plugin.handle, plugin.url_for(show_search, "n"), ListItem("New Search"), True)
    addDirectoryItem(plugin.handle, plugin.url_for(clear_search), ListItem("Clear Previous"), True)
    if path.exists(PROFILE+"/search.txt"):
        f = open(PROFILE+"/search.txt", 'r')
        terms = []
        line = f.readline()
        while not line == "":
            line = line.replace("\n", "")
            terms.append(line)
            line = f.readline()
        f.close()
        terms = terms[::-1]
        for i in range(0, len(terms)):
            if terms.index(terms[i]) == i:
                addDirectoryItem(plugin.handle, plugin.url_for(show_search, terms[i]), ListItem(terms[i]), True)
    endOfDirectory(plugin.handle)

@plugin.route('/clear_search')
def clear_search():
    remove(PROFILE+"/search.txt")
    endOfDirectory(plugin.handle, succeeded=False)

@plugin.route('/search/<keyword>')
def show_search(keyword):
    if len(keyword) < 3:
        keyword = Dialog().input("Search: ", type=INPUT_ALPHANUM)
    if keyword == "":
        return endOfDirectory(plugin.handle, succeeded=False)
    while len(keyword) < 3:
        keyword = Dialog().input("Search, must be at least 3 characters, Try Again: ", type=INPUT_ALPHANUM)
        if keyword == "":
            return endOfDirectory(plugin.handle, succeeded=False)
    addDirectoryItem(plugin.handle, "", ListItem("[B]Search For:[/B] [LIGHT]{0}[/LIGHT]".format(keyword)))
    f = open(PROFILE+"/search.txt", 'a')
    f.write(keyword+"\n")
    f.close()
    for item in kaa.search(keyword):
        li = ListItem(item["name"])
        li.setArt({'Poster':"https://www.kickassanime.rs/uploads/{0}".format(item["image"])})
        addDirectoryItem(plugin.handle, plugin.url_for(show_anime, item["slug"].split("/")[2]), li, True)
    endOfDirectory(plugin.handle)

#--  anime   --#
@plugin.route('/anime/<anime_slug>')
def show_anime(anime_slug):
    anime = kaa.get_anime(anime_slug)
    for ep in anime["episodes"]:
        slug = ep["slug"].split("/")
        li = ListItem("{0} - {1}".format(ep["createddate"][:10], ep["epnum"]))
        li.setArt({'poster':"https://www.kickassanime.rs/uploads/{0}".format(anime["image"])})
        addDirectoryItem(plugin.handle, plugin.url_for(show_episode, anime_slug, slug[3]), li, True)
    endOfDirectory(plugin.handle)

#-- episode --#
@plugin.route('/anime/<anime_slug>/<episode_slug>')
def show_episode(anime_slug, episode_slug):
    dat = kaa.get_episode(anime_slug, episode_slug)
    ani = dat["anime"]
    epi = dat["episode"]
    addDirectoryItem(plugin.handle, "", ListItem("--- Download Links ---"))
    for link in kaa.get_premium_links(epi):
        li = ListItem("{0} - {1}".format(link[2], link[1]))
        li.setArt({'poster':"https://www.kickassanime.rs/uploads/{0}".format(ani["image"])})
        addDirectoryItem(plugin.handle, link[0], li)
    endOfDirectory(plugin.handle)

def run():
    plugin.run()
