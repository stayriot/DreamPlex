# -*- coding: utf-8 -*-
'''
DreamPlex Plugin by DonDavici, 2012
 
https://github.com/DonDavici/DreamPlex

Some of the code is from other plugins:
all credits to the coders :-)

DreamPlex Plugin is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
(at your option) any later version.

DreamPlex Plugin is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
'''
#===============================================================================
# IMPORT
#===============================================================================
from Components.ActionMap import HelpableActionMap
from Components.MenuList import MenuList
from Components.Sources.List import List
from Components.Label import Label
from Components.config import config
from Components.config import NumericalTextInput

from Screens.ChoiceBox import ChoiceBox
from Screens.Screen import Screen
from Screens.MessageBox import MessageBox

from Plugins.Extensions.DreamPlex.DP_Player import DP_Player

from Plugins.Extensions.DreamPlex.DPH_Singleton import Singleton

from Plugins.Extensions.DreamPlex.__common__ import printl2 as printl
from Plugins.Extensions.DreamPlex.__plugin__ import getPlugins, Plugin

#===============================================================================
# 
#===============================================================================
def getViews():
    '''
    @param: none 
    @return: availableViewList
    '''
    printl("", "DP_View::getViews", "S")
    
    availableViewList = []
    viewList = (
            (_("List"), "DP_ListView", "DPS_ListView"), 
            #(_("Poster-Flow"), "DP_PosterView", "DPS_PosterView"), 
        )
    
    for view in viewList:
        try:
            availableViewList.append(view)
        except Exception, ex:
            printl("View %s not available in this skin" % view[1] + " exception: " + ex , __name__, "W")
    
    printl("", __name__, "C")
    return availableViewList

#===============================================================================
# 
#===============================================================================
def getViewClass():
    '''
    @param: none
    @return: DP_View Class 
    '''
    printl("", __name__, "S")
    
    printl("", __name__, "C")
    return DP_View

class DP_View(Screen, NumericalTextInput):
    '''
    '''

    ON_CLOSED_CAUSE_CHANGE_VIEW = 1
    ON_CLOSED_CAUSE_SAVE_DEFAULT = 2

    FAST_STILLPIC = False

    onNumberKeyLastChar                  = "#"
    activeSort                          = ("Default", None, False)
    activeFilter                        = ("All", (None, False), "")
    onEnterPrimaryKeys                  = None
    onLeavePrimaryKeyValuePair          = None
    onLeaveSelectKeyValuePair           = None
    currentKeyValuePair                 = None
    
    ShowSeasonsParams                   = None
    ShowEpisodesParams                  = None
    showMedia                           = False
    
    #itemsPerPage = int(8)  # @TODO should be set according the desktop size
    
    def __init__(self, session, libraryName, loadLibrary, playEntry, viewName, select=None, sort=None, filter=None):
        '''
        '''
        printl("", self, "S")
        
        printl("viewName: "+ str(viewName), self, "I")
        self.skinName = viewName[2]
        Screen.__init__(self, session)
        NumericalTextInput.__init__(self)
        self.skinName = viewName[2]
        self.select = select
        self.onFirstExecSort = sort
        self.onFirstExecFilter = filter
        
        self.libraryName = libraryName
        self.loadLibrary = loadLibrary
        self.viewName = viewName
        self._playEntry = playEntry
        
        self.playerData = None
        
        self.oldService = self.session.nav.getCurrentlyPlayingServiceReference()
        self.session.nav.stopService()
        
        self.mediaPath = config.plugins.dreamplex.mediafolderpath.value
        
        # Initialise library list
        list = []
        self["listview"] = List(list, True)
        
        self["number_key_popup"] = Label("")
        self["number_key_popup"].hide()

        self.seenPng = None
        self.unseenPng = None
            
        self["actions"] = HelpableActionMap(self, "DP_View", 
        {
            "ok":         (self.onKeyOk, ""),
            "cancel":     (self.onKeyCancel, ""),
            "left":       (self.onKeyLeft, ""),
            "right":      (self.onKeyRight, ""),
            "up":         (self.onKeyUp, ""),
            "down":       (self.onKeyDown, ""),
            "info":       (self.onKeyInfo, ""),
            "menu":       (self.onKeyMenu, ""),
            "video":      (self.onKeyVideo, ""),
            "red":        (self.onKeyRed, ""),
            #"green":      (self.onKeyGreen, ""),
            "yellow":     (self.onKeyYellow, ""),
            "blue":       (self.onKeyBlue, ""),

            "red_long":        (self.onKeyRedLong, ""),
            #"green_long":      (self.onKeyGreenLong, ""),
            #"yellow_long":     (self.onKeyYellowLong, ""),
            #"blue_long":       (self.onKeyBlueLong, ""),
            
            "bouquet_up":       (self.bouquetUp, ""),
            "bouquet_down":     (self.bouquetDown, ""),
            
            "1":       (self.onKey1, ""),
            "2":       (self.onKey2, ""),
            "3":       (self.onKey3, ""),
            "4":       (self.onKey4, ""),
            "5":       (self.onKey5, ""),
            "6":       (self.onKey6, ""),
            "7":       (self.onKey7, ""),
            "8":       (self.onKey8, ""),
            "9":       (self.onKey9, ""),
            "0":       (self.onKey0, ""),

        }, -2)
        
        # For number key input
        self.setUseableChars(u' 1234567890abcdefghijklmnopqrstuvwxyz')
        
        self.onLayoutFinish.append(self.setCustomTitle)
        self.onFirstExecBegin.append(self.onFirstExec)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def setCustomTitle(self):
        '''
        '''
        printl("", self, "S")
        
        self.setTitle(_(self.libraryName))
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onFirstExec(self):
        '''
        '''
        printl("", self, "S")        
        
        if self.select is None: # Initial Start of View, select first entry in list
            sort = False
            if self.onFirstExecSort is not None:
                self.activeSort = self.onFirstExecSort
                sort = True
            filter = False
            if self.onFirstExecFilter is not None:
                self.activeFilter = self.onFirstExecFilter
                filter = True
            
            self._load(ignoreSort=sort, ignoreFilter=filter)
            self.refresh()
        else: # changed views, reselect selected entry
            printl("self.select: " +  str(self.select), self, "D")
            sort = False
            if self.onFirstExecSort is not None:
                self.activeSort = self.onFirstExecSort
                sort = True
            filter = False
            if self.onFirstExecFilter is not None:
                self.activeFilter = self.onFirstExecFilter
                filter = True
            
            self._load(self.select[0], ignoreSort=sort, ignoreFilter=filter)
            keys = self.select[1].keys()
            listViewList = self["listview"].list
            for i in range(len(listViewList)):
                entry = listViewList[i]
                found = True
                for key in keys:
                    if entry[1][key] != self.select[1][key]:
                        found = False
                        break
                if found:
                    self["listview"].setIndex(i)
                    break
            self.refresh()
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def bouquetUp(self):
        '''
        '''
        printl("", self, "S")
        
        self["shortDescription"].pageUp()
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def bouquetDown(self):
        '''
        '''
        printl("", self, "S")
        
        self["shortDescription"].pageDown()
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def onKey1(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(1)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKey2(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(2)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKey3(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(3)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKey4(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(4)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKey5(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(5)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKey6(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(6)
        
        printl("", self, "C")

    
    #===========================================================================
    # 
    #===========================================================================
    def onKey7(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(7)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKey8(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(8)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKey9(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(9)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKey0(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNumberKey(0)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onNumberKey(self, number):
        '''
        '''
        printl("", self, "S")
        
        printl(str(number), self, "I")
        
        key = self.getKey(number)
        if key is not None:
            keyvalue = key.encode("utf-8")
            if len(keyvalue) == 1:
                self.onNumberKeyLastChar = keyvalue[0].upper()
                self.onNumberKeyPopup(self.onNumberKeyLastChar, True)
                
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onNumberKeyPopup(self, value, visible):
        '''
        '''
        printl("", self, "S")
        
        if visible:
            self["number_key_popup"].setText(value)
            self["number_key_popup"].show()
        else:
            self["number_key_popup"].hide()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def timeout(self):
        '''
        onNumberKeyTimeout
        '''
        printl("", self, "S")
        
        printl(self.onNumberKeyLastChar, self, "I")
        if self.onNumberKeyLastChar != ' ':
            self.activeFilter = ('Abc', ('title', False, 1), self.onNumberKeyLastChar)
        else:
            self.activeFilter = ("All", (None, False), ("All", ))
        self.sort()
        self.filter()
        
        self.refresh()
        
        self.onNumberKeyPopup(self.onNumberKeyLastChar, False)
        NumericalTextInput.timeout(self)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyOk(self):
        '''
        '''
        printl("", self, "S")
        
        self.onEnter()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyCancel(self):
        '''
        '''
        printl("", self, "S")
        
        self.onLeave()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyInfo(self):
        '''
        '''
        printl("", self, "S")
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def onKeyMenu(self):
        '''
        '''
        printl("", self, "S")
        
        self.displayOptionsMenu()
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def onKeyVideo(self):
        '''
        '''
        printl("", self, "S")
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyLeft(self):
        '''
        '''
        printl("", self, "S")
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def onKeyRight(self):
        '''
        '''
        printl("", self, "S")
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyUp(self):
        '''
        '''
        printl("", self, "S")
        
        self.onPreviousEntry()
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def onKeyDown(self):
        '''
        '''
        printl("", self, "S")
        
        self.onNextEntry()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyRed(self):
        '''
        '''
        printl("", self, "S")
        
        self.onToggleSort()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyRedLong(self):
        '''
        '''
        printl("", self, "S")
        
        self.onChooseSort()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyGreen(self):
        '''
        '''
        printl("", self, "S")
        
        self.onToggleFilter()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyGreenLong(self):
        '''
        '''
        printl("", self, "S")
        
        self.onChooseFilter()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyYellow(self):
        '''
        '''
        printl("", self, "S")
        
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyYellowLong(self):
        '''
        '''
        printl("", self, "S")
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyBlue(self):
        '''
        '''
        printl("", self, "S")
        
        self.onToggleView()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onKeyBlueLong(self):
        '''
        '''
        printl("", self, "S")
        
        self.onChooseView()
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def onToggleSort(self):
        '''
        '''
        printl("", self, "S")
        
        for i in range(len(self.onSortKeyValuePair)):
            if self.activeSort[1] == self.onSortKeyValuePair[i][1]:
                if (i+1) < len(self.onSortKeyValuePair):
                    self.activeSort = self.onSortKeyValuePair[i + 1]
                else:
                    self.activeSort = self.onSortKeyValuePair[0]
                break
        
        self.sort()
        self.filter()
        self.refresh()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onChooseSortCallback(self, choice):
        '''
        '''
        printl("", self, "S")
        
        if choice is not None:
            self.activeSort = choice[1]
            self.sort()
            self.filter()
            self.refresh()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onChooseSort(self):
        '''
        '''
        printl("", self, "S")
        
        menu = []
        for e in self.onSortKeyValuePair:
            menu.append((_(e[0]), e, ))
        selection = 0
        for i in range(len(self.onSortKeyValuePair)):
            if self.activeSort[1] == self.onSortKeyValuePair[i][1]:
                selection = i
                break
        self.session.openWithCallback(self.onChooseSortCallback, ChoiceBox, title=_("Select sort"), list=menu, selection=selection)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onToggleFilter(self):
        '''
        '''
        printl("", self, "S")
        
        for i in range(len(self.onFilterKeyValuePair)):
            if self.activeFilter[1][0] == self.onFilterKeyValuePair[i][1][0]:
                # Genres == Genres
                
                # Try to select the next genres subelement
                found = False
                subelements = self.onFilterKeyValuePair[i][2]
                for j in range(len(subelements)):
                    if self.activeFilter[2] == subelements[j]:
                        # Action == Action
                        if (j+1) < len(subelements):
                            y = subelements[j + 1]
                            found = True
                            break
                
                if found is True:
                    x = self.onFilterKeyValuePair[i]
                    self.activeFilter = (x[0], x[1], y, )
                else:
                    # If we are at the end of all genres subelements select the next one
                    if (i+1) < len(self.onFilterKeyValuePair):
                        x = self.onFilterKeyValuePair[i + 1]
                    else:
                        x = self.onFilterKeyValuePair[0]
                    self.activeFilter = (x[0], x[1], x[2][0], )
                
                break
        
        self.sort()
        self.filter()
        self.refresh()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onChooseFilterCallback(self, choice):
        '''
        '''
        printl("", self, "S")
        
        if choice is not None:
            self.activeFilter = choice[1]
            self.sort()
            self.filter()
            self.refresh()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onChooseFilter(self):
        '''
        '''
        printl("", self, "S")
        
        menu = []
        
        selection = 0
        counter = 0
        
        for i in range(len(self.onFilterKeyValuePair)):
            x = self.onFilterKeyValuePair[i]
            subelements = self.onFilterKeyValuePair[i][2]
            for j in range(len(subelements)):
                y = subelements[j]
                text = "%s: %s" % (_(x[0]), _(y))
                menu.append((text, (x[0], x[1], y, )))
                if self.activeFilter[1][0] == self.onFilterKeyValuePair[i][1][0]:
                    if self.activeFilter[2] == subelements[j]:
                        selection = counter
                counter += 1
        
        self.session.openWithCallback(self.onChooseFilterCallback, ChoiceBox, title=_("Select filter"), list=menu, selection=selection)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onToggleView(self):
        '''
        '''
        printl("", self, "S")
        
        select = None
        selection = self["listview"].getCurrent()
        if selection is not None:
            params = {}
            printl( "self.onEnterPrimaryKeys:" + str(self.onEnterPrimaryKeys), self, "D")
            for key in self.onEnterPrimaryKeys:
                if key != "play":
                    params[key] = selection[1][key]
            select = (self.currentKeyValuePair, params)
        
        self.close((DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW, select, self.activeSort, self.activeFilter))
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onChooseViewCallback(self, choice):
        '''
        '''
        printl("", self, "S")
        
        if choice is not None:
            select = None
            selection = self["listview"].getCurrent()
            if selection is not None:
                params = {}
                printl( "self.onEnterPrimaryKeys:" + str(self.onEnterPrimaryKeys), self, "D")
                for key in self.onEnterPrimaryKeys:
                    if key != "play":
                        params[key] = selection[1][key]
                select = (self.currentKeyValuePair, params)
            self.close((DP_View.ON_CLOSED_CAUSE_CHANGE_VIEW, select, self.activeSort, self.activeFilter, choice[1]))
            
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onChooseView(self):
        '''
        '''
        printl("", self, "S")
        
        menu = getViews()
        selection = 0
        for i in range(len(menu)):
            if self.viewName[1] == menu[i][1]:
                selection = i
                break
        self.session.openWithCallback(self.onChooseViewCallback, ChoiceBox, title=_("Select view"), list=menu, selection=selection)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onNextEntry(self):
        '''
        '''
        printl("", self, "S")
        
        self.refresh()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onPreviousEntry(self):
        '''
        '''
        printl("", self, "S")
        
        self.refresh()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onNextPage(self):
        '''
        '''
        printl("", self, "S")
        itemsTotal = self["listview"].count()
        index = self["listview"].getIndex()
        
        if index >= itemsTotal:
            index = itemsTotal - 1
        self["listview"].setIndex(index)
        self.refresh()
    
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onPreviousPage(self):
        '''
        '''
        printl("", self, "S")
        index = self["listview"].getIndex()
        
        if index < 0:
            index = 0
        self["listview"].setIndex(index)
        
        self.refresh()
    
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onEnter(self):
        '''
        '''
        printl("", self, "S")
        
        selection = self["listview"].getCurrent()
        
        if selection is not None:
            details         = selection[1]
            extraData       = selection[2]
            image           = selection[3]
            
            #details
            viewMode        = details['viewMode']
            server          = details['server']
            
            #extraData
            url_path        = extraData['key']
        
        
            if (viewMode == "ShowSeasons"):
                printl("viewMode -> ShowSeasons", self, "I")

                params = {}
                params["viewMode"] = viewMode
                params["url"] = "http://" + server + url_path
                
                self.currentSeasonsParams = params

                self._load(params)

            elif (viewMode == "ShowEpisodes"):
                printl("viewMode -> ShowEpisodes", self, "I")

                params = {}
                params["viewMode"] = viewMode
                params["url"] = "http://" + server + url_path
                
                self.currentEpisodesParams = params
                
                self._load(params)
            
            elif (viewMode == "play"):
                printl("viewMode -> play", self, "I")
                self.playEntry(selection)
                

            else:
                printl("SOMETHING WENT WRONG", self, "W")
                
        self.refresh()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def onLeave(self):
        '''
        '''
        printl("", self, "S")
        
        selectKeyValuePair = self.onLeaveSelectKeyValuePair
        printl("selectKeyValuePair: " + str(selectKeyValuePair), self, "D")
        
        if selectKeyValuePair == "backToSeasons":
            self._load(self.ShowSeasonsParams)
        
        elif selectKeyValuePair == "backToShows":
            self._load()
            
        else:
            self.close()
            printl("", self, "C")
            return
        
        self.refresh()
        
        # TODO REACTIVATE
        #=======================================================================
        # for i in range(len(self.listViewList)):
        #    entry = self.listViewList[i][1]
        #    printl("iterator: " + str(i) + " entry: " + str(entry), self, "I")
        #    isIndex = True
        #    
        #    for key in selectKeyValuePair.keys():
        #        if entry[key] != selectKeyValuePair[key]:
        #            isIndex = False
        #            break
        #    if isIndex:
        #        self["listview"].setIndex(i)
        #        break
        #=======================================================================
        
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def _load(self, primaryKeys=None, ignoreSort=False, ignoreFilter=False):
        '''
        '''
        printl("", self, "S")

        library = self.loadLibrary(primaryKeys)
        #printl("library: " + str(library), self, "D")
        self.listViewList = library[0]
        #printl("listViewList: " + str(library[0]), self, "D")
        
        self.onEnterPrimaryKeys = library[1]
        printl("onEnterPrimaryKeys: " + str(library[1]), self, "D")
        
        self.onLeavePrimaryKeyValuePair = library[2]
        printl("onLeavePrimaryKeyValuePair: " + str(library[2]), self, "D")
        
        self.onLeaveSelectKeyValuePair = library[3]
        printl("onLeaveSelectKeyValuePair: " + str(library[3]), self, "D")
        
        self.onSortKeyValuePair = library[4]
        printl("onSortKeyValuePair: " + str(library[4]), self, "D")
        
        self.onFilterKeyValuePair = library[5]
        printl("onFilterKeyValuePair: " + str(library[5]), self, "D")
        
        if len(library) >= 7:
            self.libraryFlags = library[6]
        else:
            self.libraryFlags = {}
        
    
        if ignoreSort is False:
            # After changing the lsit always return to the default sort
            self.activeSort = self.onSortKeyValuePair[0]
        
        if ignoreFilter is False:
            # After changing the lsit always return to the default filter
            x = self.onFilterKeyValuePair[0]
            self.activeFilter = (x[0], x[1], x[2][0], )
        
        self.sort()
        self.filter()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def sort(self):
        '''
        '''
        printl("", self, "S")
        #printl("listViewList: " + str(self.listViewList), self, "D")
        
        try:
            if self.activeSort[1] is None:
                printl("sorting by default", self, "D")
                self.listViewList.sort(key=lambda x: x[0], reverse=self.activeSort[2])
            else:
                printl("sorting by value in selection", self, "D")
                self.listViewList.sort(key=lambda x: x[1][self.activeSort[1]], reverse=self.activeSort[2])
        except Exception, ex:
            printl("Exception(" + str(ex) + ")", self, "E")
            
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def filter(self):
        '''
        '''
        printl("", self, "S")
        
        printl( "self.activeFilter: " + str(self.activeFilter), self, "D")
        
        listViewList = []
        if self.activeFilter[1][0] is None:
            listViewList = self.listViewList
        else:
            
            testLength = None
            if len(self.activeFilter[1]) >= 3:
                testLength = self.activeFilter[1][2]
            
            if self.activeFilter[1][1]:
                listViewList = [x for x in self.listViewList if self.activeFilter[2] in x[1][self.activeFilter[1][0]]]
            else:
                if testLength is None:
                    listViewList = [x for x in self.listViewList if x[1][self.activeFilter[1][0]] == self.activeFilter[2]]
                else:
                    listViewList = [x for x in self.listViewList if x[1][self.activeFilter[1][0]].strip()[:testLength] == self.activeFilter[2].strip()[:testLength]]
        
        self["listview"].setList(listViewList)
        self["listview"].setIndex(0)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def setText(self, name, value, ignore=False, what=None):
        '''
        
        @todo: lets check this. seems to be some kind of too much
        
        '''
        printl("", self, "S")
        
        try:
            if self[name]:
                if len(value) > 0:
                    self[name].setText(value)
                elif ignore is False:
                    if what is None:
                        self[name].setText(_("Not available"))
                    else:
                        self[name].setText(what + ' ' + _("not available"))
                else:
                    self[name].setText(" ")
        except Exception, ex:
            printl("Exception: " + str(ex), self)
            
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def refresh(self):
        '''
        '''
        printl("", self, "S")
        
        selection = self["listview"].getCurrent()
                
        self._refresh(selection)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def _refresh(self, selection):
        '''
        '''
        printl("", self, "S")
        
        printl("", self, "C")

    #===============================================================================
    # 
    #===============================================================================
    def playEntry(self, selection):
        '''
        '''
        printl("", self, "S")
        media_id = selection[1]['ratingKey']
        server = selection[1]['server']
        
        self.playerData = Singleton().getPlexInstance().playLibraryMedia(media_id, server, False)
        
        resumeStamp = self.playerData['resumeStamp']
        printl("resumeStamp: " + str(resumeStamp), self, "I")
        
        if resumeStamp > 0:
            self.session.openWithCallback(self.handleResume, MessageBox, _(" This file was partially played.\n\n Do you want to resume?"), MessageBox.TYPE_YESNO)
        
        else:
            self.session.open(DP_Player, self.playerData)
            #self.session.open(DP_Proxy, self.playerData)
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def handleResume(self, confirm):
        '''
        '''
        printl("", self, "S")
        
        resume = False
        
        if confirm:
            resume = True
            self.session.open(DP_Player, self.playerData, resume)
        
        else:
            self.session.open(DP_Player, self.playerData)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def setDefaultView(self, unused=None, unused2=None):
        '''
        '''
        printl("", self, "S")

        select = None
        selection = self["listview"].getCurrent()
        if selection is not None:
            primaryKeyValuePair = {}
            printl( "self.onEnterPrimaryKeys: " + str(self.onEnterPrimaryKeys), self, "D")
            for key in self.onEnterPrimaryKeys:
                if key != "play":
                    primaryKeyValuePair[key] = selection[1][key]
            select = (self.currentKeyValuePair, primaryKeyValuePair)
        self.close((DP_View.ON_CLOSED_CAUSE_SAVE_DEFAULT, select, self.activeSort, self.activeFilter))
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def clearDefaultView(self, unused=None, unused2=None):
        '''
        '''
        printl("", self, "S")
        
        self.close((DP_View.ON_CLOSED_CAUSE_SAVE_DEFAULT, ))
        
        printl("", self, "C")

    
    #===========================================================================
    # 
    #===========================================================================
    def displayOptionsMenu(self):
        '''
        '''
        printl("", self, "S")
        
        functionList = []
        
        functionList.append((_("Mark media unwatched"), Plugin("View", fnc=self.markUnwatched), ))
        functionList.append((_("Mark media watched"), Plugin("View", fnc=self.markWatched), ))
        functionList.append((_("Initiate Library refresh"), Plugin("View", fnc=self.initiateRefresh), ))
        #functionList.append((_("Delete media from Library"), Plugin("View", fnc=self.deleteFromLibrary), ))
        
        self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, \
            title=_("Media Functions"), list=functionList)
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def markUnwatched(self, unused=None, unused2=None):
        '''
        '''
        printl("", self, "S")

        Singleton().getPlexInstance().getURL(self.unseenUrl)
        self.showMessage()
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def markWatched(self, unused=None, unused2=None):
        '''
        '''
        printl("", self, "S")
        
        Singleton().getPlexInstance().getURL(self.seenUrl)
        self.showMessage()
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def initiateRefresh(self, unused=None, unused2=None):
        '''
        '''
        printl("", self, "S")
        
        Singleton().getPlexInstance().getURL(self.refreshUrl)
        self.showMessage()
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def deleteFromLibrary(self, unused=None, unused2=None):
        '''
        '''
        printl("", self, "S")
        
        self.session.openWithCallback(self.executeLibraryDelete, MessageBox, _("Are you sure?"), MessageBox.TYPE_YESNO)
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def executeLibraryDelete(self, confirm):
        '''
        '''
        printl("", self, "S")
        
        if confirm:
            Singleton().getPlexInstance().getURL(self.deleteUrl)
            self.showMessage()
        else:
            self.session.open(MessageBox,_("Deleting aborted!"), MessageBox.TYPE_INFO)
        
        printl("", self, "C")
        
    #===========================================================================
    # 
    #===========================================================================
    def showMessage(self):
        '''
        '''
        printl("", self, "S")
        
        self.session.open(MessageBox,_("You have to reenter the section to see the changes!"), MessageBox.TYPE_INFO)
        
        printl("", self, "C")
    
    #===========================================================================
    # 
    #===========================================================================
    def displayViewMenu(self):
        '''
        '''
        printl("", self, "S")
        
        pluginList = []
        
        pluginList.append((_("Set view as default"), Plugin("View", fnc=self.setDefaultView), ))
        pluginList.append((_("Clear default view"), Plugin("View", fnc=self.clearDefaultView), ))
        
        plugins = getPlugins(where=Plugin.MENU_MOVIES_PLUGINS)
        for plugin in plugins:
            pluginList.append((plugin.name, plugin, ))
        
        if len(pluginList) == 0:
            pluginList.append((_("No plugins available"), None, ))
        
        self.session.openWithCallback(self.displayOptionsMenuCallback, ChoiceBox, \
            title=_("Options"), list=pluginList)
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def pluginCallback(self, args=None):
        '''
        '''
        printl("", self, "S")
        
        self.refresh()
        
        printl("", self, "C")

    #===========================================================================
    # 
    #===========================================================================
    def displayOptionsMenuCallback(self, choice):
        '''
        '''
        printl("", self, "S")
        
        if choice is None or choice[1] is None:
            return
        
        selection = self["listview"].getCurrent()
        if selection is not None:
            if choice[1].start:
                if choice[1].supportStillPicture:
                    self.session.open(choice[1].start, selection[1])
                else:
                    if self.has_key("backdrop"):
                        self["backdrop"].finishStillPicture()
                    self.session.openWithCallback(self.pluginCallback, choice[1].start, selection[1])
                    
            elif choice[1].fnc:
                if choice[1].supportStillPicture is False and self.has_key("backdrop"):
                    self["backdrop"].finishStillPicture()
                choice[1].fnc(self.session, selection[1])
                if choice[1].supportStillPicture is False and self.has_key("backdrop"):
                    self.refresh()
        
        printl("", self, "C")
