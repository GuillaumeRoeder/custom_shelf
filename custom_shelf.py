
###############################################################################
# Name:
#   CustomShelf.py
#
# Description:
#   load a customable shelf for animation departement.
#
# Author:
#   Guillaume Roeder
#
# Copyright (C) 2022 Guillaume Roeder. All rights reserved.
###############################################################################
from maya import cmds 
import re
import os


class CustomShelf():
    """
    Creates a shelf pointing to a given folder. 
    scripts inside the folder are added to the shelf, and subfolders make popup buttons.
    """

    def __init__(self, shelf_directory="", shelf_name="name"):

        self.shelf_directory = shelf_directory # Path to the tool folder
        self.icon_path = os.path.join(self.shelf_directory, "icons") # path to the icon folder
        self.shelf_name = shelf_name

        self.categories = list()
        self.popup_tool_dict =  dict() # keys are the tool names (directories), values are the full path to the tools (scripts) inside the directory  
        self.tool_paths = dict()
        self.popup_menus = dict() # keys are tool-names and values are popup menu parented to the keys
        self.shelf = None

        self.get_all_tools(self.shelf_directory)
    
    def __repr__(self):
        return "CustomShelf(tool_directory={}, shelf_nam={})".format(self.tool_directory, self.shelf_name)

    def __str__(self):
        return self.shelf

    def get_tools_from_dir(self, directory, category):
        """
        Find and gather all python and mel tools in a given directory
        """        

        self.tool_paths[category] = list()
        category_dir = os.path.join(directory, category)
        for tool_file in os.listdir(category_dir):
            
            # filter out dcc commands and non-python / non-mel scripts
            if re.search("(.py|.mel)$", tool_file) and not re.search("(_dcc.py|_dcc.mel)$", tool_file):
                self.tool_paths[category].append(os.path.join(category_dir, tool_file))
  
    def get_popup_tools_from_dir(self, directory, category):
        """
        Find and gather all tools as folders in a given directory
        """     
        
        category_dir = os.path.join(directory, category)
        temp_dict = dict()
        # Find all popup tools (directory tools)
        for tool in os.listdir(category_dir):
            tool_path = os.path.join(category_dir, tool)
            if os.path.isdir(tool_path):
                temp_dict[tool_path] = [os.path.join(tool_path, i) for i in os.listdir(tool_path)]

                # filter out dcc commands and non-python / non-mel scripts
                for item_path in temp_dict[tool_path]:
                    if re.search("(_dcc.py|_dcc.mel)$", item_path) or not re.search("(.py|.mel)$", item_path):
                        temp_dict[tool_path].remove(item_path)
                        
        self.popup_tool_dict[category] = temp_dict
                        
    def get_all_tools(self, shelf_directory):
        """
        Gather all tools
        """

        if not os.path.exists(shelf_directory):
            return

        self.categories = os.listdir(shelf_directory)
        self.categories.sort()
        if "icons" in self.categories:
            self.categories.remove("icons")

        for category in self.categories:
            self.get_tools_from_dir(shelf_directory, category)
            self.get_popup_tools_from_dir(shelf_directory, category)
            
    def add_buttons_from_path(self, tool_paths):
        """
        Add all tools to the shelf
        tool_path : list(str)
        shelf : shelf object
        """

        shelf_butons = []
        for path in tool_paths:
            tool_name = self.filter_py_mel(path)[0]
            command1 = self.filter_py_mel(path)[1]
            icon = self.find_icon(tool_name)
            
            command2_script = self.find_dcc_command(path)
            command2 = self.filter_py_mel(command2_script)[1]

            tool_name = tool_name.replace("_", " ")
            button = cmds.shelfButton(l=tool_name ,command=command1, image=icon, parent=self.shelf, doubleClickCommand=command2)
            
            shelf_butons.append(button)
        
        return shelf_butons

    def add_popup_button_from_paths(self, popup_tool_dict):
        """
        Add all popup buttons to the shelf
        popup_tool_dict : dict( str : list(str) )
        shelf : shelf object
        """
        
        for tool_path in popup_tool_dict.keys():
            tool_name = os.path.basename(tool_path) # tool is a directory so no need to remove extension
            button_script_path = None

            for script_path in popup_tool_dict[tool_path]:     
                script_file = os.path.basename(script_path) 

                # look for a command with the same name as the directory
                if re.search("({})(.py|.mel)$".format(tool_name), script_file):
                    button_script_path = script_path
                    popup_tool_dict[tool_path].remove(script_path)
                    break

            # add the command to the button if it exists
            if button_script_path is not None:
                new_button = self.add_buttons_from_path([button_script_path])[0]
            else:
                icon = self.find_icon(tool_name)
                new_button = cmds.shelfButton(l=tool_name, image=icon, parent=self.shelf)

            # Add menus 
            self.popup_menus[tool_name] = cmds.shelfButton(new_button, q=True, popupMenuArray=True)[0]
            for script_path in popup_tool_dict[tool_path]:
                if re.search("__init__.py$", script_path):
                    continue
                filters = self.filter_py_mel(script_path)
                item_name = filters[0]
                command = filters[1]
                
                item_name = item_name.replace("_", " ")
                cmds.menuItem(label=item_name, sourceType="python", parent=self.popup_menus[tool_name], command=command)

    def add_menu_item(self, item_name, button_name, language, command):
        """
        handy way to add menus to an existing popup button
        """
        popup_menu = self.popup_menus[button_name]
        item = cmds.menuItem(label=item_name, sourceType="python", parent=popup_menu, command=command)
        return item

    def add_command(self, tool_name, language="python", icon_path=None, command="", dcc_command=""):
        """
        Useful to add short commands to the shelf
        """

        if icon_path is None:
            icon_path = self.find_icon(tool_name)

        cmds.shelfButton(l=tool_name ,command=command, sourceType=language, image=icon_path, parent=self.shelf, doubleClickCommand=dcc_command)

    def create_separator(self):
        cmds.separator(width=12, height=35, style="shelf", horizontal=False, parent=self.shelf)

    def reload_shelf(self):
        cmds.deleteUI(self.shelf_name)
        self.create_shelf()

    def create_shelf(self):

        if not cmds.shelfLayout(self.shelf_name, q=True, exists=True):
            self.shelf = cmds.shelfLayout(self.shelf_name, parent="ShelfLayout")
            for category in self.categories:
                self.add_buttons_from_path(self.tool_paths[category])
                self.add_popup_button_from_paths(self.popup_tool_dict[category])
                self.create_separator() 
            return
        
        self.reload_shelf()
        
    
    ###### Utils #######

    def find_dcc_command(self, script_path):
        """
        Find if dcc (double click command) exists in the folder
        """

        dcc_script_without_extention = os.path.join(os.path.dirname(script_path), os.path.basename(script_path).split(".")[0]) 
        mel_script =  dcc_script_without_extention + "_dcc.mel"
        python_script = dcc_script_without_extention + "_dcc.py"
        if os.path.exists(mel_script):
            return mel_script
        elif os.path.exists(python_script):
            return python_script
        
        return ""

    def find_icon(self, tool_name):
        """
        Find coresponding icon for given tool_name
        """

        tool_icon_file = "commandButton.png" # set default icon
        if not os.path.exists(self.icon_path):
            os.makedirs(self.icon_path)
            return tool_icon_file
            
        # Look for conresponding icons in the ICON_PATH: Icons have the same name as their tools.
        for icon_file in os.listdir(self.icon_path):
            # Every format is supported
            if re.search("({})(.png|.jpg|jpeg|.svg)$".format(tool_name), icon_file):
                tool_icon_file=icon_file
                break

        return os.path.join(self.icon_path, tool_icon_file)

    def filter_py_mel(self, file_path):
        """
        Filter python and mel script, assigning the right command for the tool and extracting the tool_name frome the file name
        """
        
        tool_name = ""
        command = ""

        # Create arguments for python files
        if re.search(".py$", file_path):
            tool_name = re.sub('.py$', '', os.path.basename(file_path))
            command = 'exec(open("{}").read())'.format(file_path)
        
        # Create arguments for mel files
        elif re.search(".mel$", file_path):
            tool_name = re.sub('.mel$', '', os.path.basename(file_path))
            command = 'import maya.mel; maya.mel.eval(\'source "{}"\')'.format(file_path)
        
        return tool_name, command





########################################################################
# execution
########################################################################

import imp

path_to_module = "path to module"
module = imp.load_source("module.name", path_to_module)

shelf = module.CustomShelf("path to shelf folder", "shelf name")
shelf.create_shelf()
