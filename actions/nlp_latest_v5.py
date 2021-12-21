# -*- coding: utf-8 -*-
import numpy as np
import requests
import string
from bs4 import BeautifulSoup
import nltk
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
from unicodedata import numeric
from nltk.stem import WordNetLemmatizer
nltk.download('wordnet')
import re
import random
import pandas as pd
#https://stackoverflow.com/questions/28639677/capitalize-the-first-letter-after-a-punctuation/28639714
#https://stackoverflow.com/questions/68640360/python-replace-fractions-in-a-string
from beautifultable import BeautifulTable
from pattern.en import pluralize, singularize
from nltk.util import ngrams
from nltk.tokenize import RegexpTokenizer
from fractions import Fraction


URL = "https://www.allrecipes.com/recipe/11679/homemade-mac-and-cheese/"
URL_nonveg = 'https://www.allrecipes.com/recipe/258947/mushroom-beef-burgers/'
URL_unhealthy = 'https://www.allrecipes.com/recipe/8338/cannoli-with-chocolate-chips/'
main_path = "data/"
extra_path = "extra/"
#non_veg_file_path = main_path + "list_of_non_veg_items.txt"
#veg_subs_path = main_path + "list_of_veg_substitutes.txt"
veg_subs_path = main_path + "veg_subs.csv"
tools_path = main_path + "list_of_tools.txt"
cooking_method_path = main_path + "list_of_cooking_methods.txt"
healthy_ingredients_subs_path = main_path + "healthy_ingredients_subs.csv"
healthy_steps_subs_path = main_path + "healthy_steps.csv"
chinese_ingredients_subs_path = main_path + "chinese_ingredients_subs.csv"
indian_ingredients_subs_path = main_path + "indian_ingredients_subs.csv"
cheap_ingredients_subs_path = main_path + "cheap_subs.csv"
gluten_free_ingredients_subs_path = main_path + "gluten_subs.csv"
implied_tools_path = main_path + "implied_tools.csv"
additional_descriptor_file_path = main_path + "list_descriptor.txt"
additional_preperation_file_path = main_path + "list_preperation.txt"
additional_ingredients_file_path = main_path + "list_ingredients.txt"

dairy_list_path = extra_path + "dairy_list.txt"
fruit_list_path = extra_path + "fruit_list.txt"
grain_list_path = extra_path + "grain_list.txt"
nonveg_list_path = extra_path + "non_veg_list.txt"
nut_list_path = extra_path + "nut_list.txt"
pulses_list_path = extra_path + "pulses_list.txt"
spices_list_path = extra_path + "spices_list.txt"
veggie_list_path = extra_path + "veggie_list.txt"
herb_list_path = extra_path + "herb_list.txt"
sauce_list_path = extra_path + "sauces_list.txt"

class Ingredient:

  def __init__(self,fullname=None,main_ingredients=None,quantity_type=None,quantity = None,units=None,descriptor=None,preparation=None,step_indexes=[],ingredient_type='General'):  
    self.fullname = fullname
    self.main_ingredients = main_ingredients
    self.quantity_type = quantity_type
    self.quantity = quantity
    self.units = units
    self.descriptor = descriptor
    self.preparation = preparation
    self.step_indexes = step_indexes
    self.ingredient_type=ingredient_type

  def print_ingredient(self):
    print('Full Name: ',self.fullname)
    print("Main Ingredient: ",self.main_ingredients)
    print("Quantity Type: ",self.quantity_type)
    print("Quantity: ",self.quantity)
    print("Units: ",self.units)
    print('Descriptor: ',self.descriptor)
    print('Preparation: ',self.preparation)
    print('Used in steps',self.step_indexes)
    print('Ingredient Type', self.ingredient_type,'\n')

class Step:
  def __init__(self,full_step=None,ingredients=[],tools=[],methods = [],times=None,index=None):  
    self.full_step = full_step
    self.ingredients = ingredients
    self.tools = tools
    self.methods = methods
    self.times = times
    self.index = index
  
  def print_steps(self):
    print('Step number: ',self.index)
    print('Full Step: ',self.full_step)
    print("Ingredients: ",end='')
    for ingredient in self.ingredients:
      print(ingredient.fullname,end=',')
    print("\nTools: ",self.tools)
    print("Methods: ",self.methods)
    print("Times: ",self.times,'\n')

class Recipe:
  def __init__(self,title=None,Ingredients=None,Tools=None,Methods=None,Steps=None,URL=None):  
    self.title=title
    self.Ingredients = Ingredients
    self.Tools = Tools
    self.Methods = Methods
    self.Steps = Steps
    self.URL = URL
    self.primary_cooking_method= None
  
  def print_recipie(self):
    if (self.title):
        print('Name of recipie: ',self.title)
    print('URL: ',self.URL)
    if (self.primary_cooking_method):
        print('Primary Cooking Method: ',self.primary_cooking_method)
    print('Required_Tools:',','.join(self.Tools))
    print('Used Methods:',','.join(self.Methods))
    self.print_table_ingredients()
    self.print_table_steps()

  
  def print_table_ingredients(self):
    table = BeautifulTable(maxwidth=130)
    table.columns.header = ["Full Name", "Main Ingredient", "Ingredient_Type","Quantity Type","Quantity","Units","Descriptor","Preperation","Used in steps"]
    for ingredient in self.Ingredients:
      table.rows.append([ingredient.fullname,ingredient.main_ingredients,ingredient.ingredient_type,ingredient.quantity_type,ingredient.quantity,ingredient.units,ingredient.descriptor,ingredient.preparation,ingredient.step_indexes])
    print(table)
  
  def print_table_steps(self):
    table = BeautifulTable(maxwidth=130)
    table.columns.header = ["Step", "Full Step", "Ingredients","Tools","Methods","Times"]
    for step in self.Steps:
      step_ingredients = []
      for ingredient in step.ingredients:
        step_ingredients.append(ingredient.fullname)
      table.rows.append([step.index,step.full_step,';'.join(step_ingredients),','.join(step.tools),','.join(step.methods),step.times])
    print(table)

  def substitute_ingredient_fn(self,old_ingredient, substitute_ingredient):
    
    index_of_ingredient = 0
    print('Replacing',old_ingredient,'with',substitute_ingredient)

    for i in range(len(self.Ingredients)):
      if old_ingredient.lower() in self.Ingredients[i].fullname.lower() or old_ingredient.lower() in self.Ingredients[i].main_ingredients.lower():
        self.Ingredients[i].fullname = substitute_ingredient
        self.Ingredients[i].main_ingredients = substitute_ingredient
        index_of_ingredient = i
        break
       
    for i in self.Ingredients[index_of_ingredient].step_indexes:
      #self.Steps[i].full_step = re.sub(old_ingredient, substitute_ingredient, self.Steps[i].full_step, flags=re.IGNORECASE) 
      self.Steps[i].full_step = tokenize_and_sub(self.Steps[i].full_step,old_ingredient,substitute_ingredient)
      for j in range(len(self.Steps[i].ingredients)):
        if old_ingredient.lower() in self.Steps[i].ingredients[j].fullname.lower() or old_ingredient.lower() in self.Steps[i].ingredients[j].main_ingredients.lower():
          self.Steps[i].ingredients[j] = self.Ingredients[index_of_ingredient]
          break

  def substitute_step_fn(self,old_step, new_step):
    
    print('Replacing',old_step,'with',new_step)

    index_of_ingredient = 0

    for i in range(len(self.Methods)):
      if old_step.lower() in self.Methods[i].lower():
        self.Methods[i] = new_step
    
    for i in range(len(self.Steps)):
      if old_step.lower() in self.Steps[i].full_step.lower() or old_step.lower() in self.Steps[i].full_step.lower():
        self.Steps[i].full_step = re.sub(old_step, new_step, self.Steps[i].full_step, flags=re.IGNORECASE) 
        for j in range(len(self.Steps[i].methods)):
          if old_step.lower() in self.Steps[i].methods[j]:
            self.Steps[i].methods[j] = new_step
        
  def to_veg(self):
    check=False
    df_ingredients = pd.read_csv(veg_subs_path)
    df_ingredients = df_ingredients.to_numpy()
    for i in range(len(self.Ingredients)):
      for item,substitute_ingredient in df_ingredients:
        #if item.lower() in self.Ingredients[i].fullname.lower() or item.lower() in self.Ingredients[i].main_ingredients.lower():
        if match_ingredient(item,self.Ingredients[i]):
          self.substitute_ingredient_fn(item, substitute_ingredient)
          check=True
          break
    
    if check:
        print('Transforming recipie to Veg complete')
    else:
        print('I couldnt find a suitable substituiton. Sorry!')
    
    return check
    
  def ratio(self,ratio_num):
    print('Transforming ratio of ingredients to',ratio_num)
    for i in range(len(self.Ingredients)):
      for j in self.Ingredients[i].step_indexes:
        if (' '.join((self.Ingredients[i].quantity,self.Ingredients[i].units))) in self.Steps[j].full_step:
           if (self.Ingredients[i].quantity.isnumeric()):
               old_str =' '.join((self.Ingredients[i].quantity,self.Ingredients[i].units))
               new_quantity = str(float(self.Ingredients[i].quantity) * ratio_num)
               new_str = ' '.join((new_quantity,self.Ingredients[i].units))
               self.Steps[j].full_step = self.Steps[j].full_step.replace(old_str,new_str)
      
      if self.Ingredients[i].quantity.isnumeric():
        self.Ingredients[i].quantity=float(self.Ingredients[i].quantity)*ratio_num
         

  def to_healthy(self):
    check=False
    print('Transforming recipie to healthy')
    df_ingredients = pd.read_csv(healthy_ingredients_subs_path)
    df_ingredients = df_ingredients.to_numpy()

    df_steps = pd.read_csv(healthy_steps_subs_path)
    df_steps= df_steps.to_numpy()

    for i in range(len(self.Ingredients)):
      if 'salt' in self.Ingredients[i].fullname.lower() or 'salt' in self.Ingredients[i].main_ingredients.lower():
        if (self.Ingredients[i].quantity.isnumeric()):
            self.Ingredients[i].quantity *= 0.5
        print("Use half the quantity of salt")
        check=True
      if 'butter' in self.Ingredients[i].fullname.lower() or 'butter' in self.Ingredients[i].main_ingredients.lower():
        if (self.Ingredients[i].quantity.isnumeric()):
            self.Ingredients[i].quantity *= 0.75
        print("Use 3/4th the quantity of butter")
        check=True
      for unhealthy_item,substitute_ingredient in df_ingredients:
        #if unhealthy_item.lower() in self.Ingredients[i].fullname.lower() or unhealthy_item.lower() in self.Ingredients[i].main_ingredients.lower():
        if match_ingredient(unhealthy_item,self.Ingredients[i]):
          self.substitute_ingredient_fn(unhealthy_item, substitute_ingredient)
          check=True
          break
  
    for i in range(len(self.Steps)):
      for unhealthy_step,substitute_step in df_steps:
          if unhealthy_step in self.Steps[i].full_step.lower():
            self.substitute_step_fn(unhealthy_step, substitute_step)  
            check=True
    
    if check:
        print('Transforming recipie to Healthy complete')
    else:
        print('This recipie is as healthy as I can make it. Sorry!')
    
    return check

  def to_chinese(self):
    check = False
    print('Transforming recipie to Chinese')
    df_ingredients = pd.read_csv(chinese_ingredients_subs_path)
    df_ingredients = df_ingredients.to_numpy()

    for i in range(len(self.Ingredients)):
      for item,substitute_ingredient in df_ingredients:
        #if item.lower() in self.Ingredients[i].fullname.lower() or item.lower() in self.Ingredients[i].main_ingredients.lower():
        if match_ingredient(item,self.Ingredients[i]):
          self.substitute_ingredient_fn(item, substitute_ingredient)
          check=True
          break
    
    if check:
        print('Transforming recipie to Chinese complete')
    else:
        print('I couldnt find a suitable substituiton. Sorry!')
    
    return check
  
  def to_indian(self):
    check=False
    print('Transforming recipie to Indian')
    df_ingredients = pd.read_csv(indian_ingredients_subs_path)
    df_ingredients = df_ingredients.to_numpy()

    for i in range(len(self.Ingredients)):
      for item,substitute_ingredient in df_ingredients:
        #if item.lower() in self.Ingredients[i].fullname.lower() or item.lower() in self.Ingredients[i].main_ingredients.lower():
        if match_ingredient(item,self.Ingredients[i]):
          self.substitute_ingredient_fn(item, substitute_ingredient)
          check=True
          break
    
    if check:
        print('Transforming recipie to Indian complete')
    else:
        print('I couldnt find a suitable substituiton. Sorry!')
    
    return check
  
  def to_cheap(self):
    check=False
    print('Transforming recipie to cheaper recipie')
    df_ingredients = pd.read_csv(cheap_ingredients_subs_path)
    df_ingredients = df_ingredients.to_numpy()

    for i in range(len(self.Ingredients)):
      for item,substitute_ingredient in df_ingredients:
        #if item.lower() in self.Ingredients[i].fullname.lower() or item.lower() in self.Ingredients[i].main_ingredients.lower():
        if match_ingredient(item,self.Ingredients[i]):
            self.substitute_ingredient_fn(item, substitute_ingredient)
            check=True
            break
    
    if check:
        print('Transforming recipie to cheap complete')
    else:
        print('I couldnt find a suitable substituiton. Sorry!')
    
    return check
        
  def to_gluten_free(self):
    check=False
    print('Transforming recipie to gluten free recipie')
    df_ingredients = pd.read_csv(gluten_free_ingredients_subs_path)
    df_ingredients = df_ingredients.to_numpy()

    for i in range(len(self.Ingredients)):
      for item,substitute_ingredient in df_ingredients:
        #if item.lower() in self.Ingredients[i].fullname.lower() or item.lower() in self.Ingredients[i].main_ingredients.lower():
        if match_ingredient(item,self.Ingredients[i]):
          self.substitute_ingredient_fn(item, substitute_ingredient)
          check=True
          break
    
    if check:
        print('Transforming recipie to gluten free complete')
    else:
        print('I couldnt find a suitable substituiton. Sorry!')
    
    return check
           
def get_recipie_from_URL(URL):
  myRecipie = Recipe()
  myRecipie.URL = URL
  page = requests.get(URL)
  soup = BeautifulSoup(page.content, "html.parser")
  title_parse = soup.find_all("h1", class_="headline heading-content elementFont__display")
  if len(title_parse)>=1:
    title_text = title_parse[0].text
    if not isinstance(title_text, str):
        title_text = title_unicode.encode("ascii", "ignore").translate(None, string.punctuation).strip()
        myRecipie.title = title_text
  ingredient_parse = soup.find_all("input", class_="checkbox-list-input")
  direction_parse = soup.find_all("div", class_="paragraph")
  unicode_quantities = []
  unicode_units = []
  unicode_ingredients = []
  unicode_type = []

  #----------------------------Half Parsing Directions-------------------------#
  directions = []

  for step in direction_parse:
    step_text = step.text
    step_text.encode("ascii", "ignore").strip()
    step_text = step.text.replace('fat free','fat-free')
    step_text = fix_fraction(step_text)
    directions.append(step_text)

  #--------------------------Half Parsed Directions are ready------------------#

  #----------------------------Parsing Ingredients-----------------------------#
  for ingredient in ingredient_parse:
    val = ingredient.attrs
    if u'data-quantity' in val.keys():
        unicode_quantities.append(val[u'data-init-quantity'])
    if u'data-unit' in val.keys():
        unicode_units.append(val[u'data-unit'])
    if u'data-ingredient' in val.keys():
        unicode_ingredients.append(val[u'data-ingredient'])
    if u'data-ingredient' in val.keys():
        unicode_type.append(val[u'data-unit_family'])

  quantities = unicode_quantities
  units = unicode_units
  ingredients = unicode_ingredients
  quantity_type = unicode_type
  descriptor  = [''] * len(ingredients)
  preparation = [''] * len(ingredients)
  main_ingredients = [''] * len(ingredients)

  with open(additional_descriptor_file_path) as file:
     lines = file.readlines()
     list_of_additional_descriptors = [line.rstrip() for line in lines] 
  
  with open(additional_preperation_file_path) as file:
     lines = file.readlines()
     list_of_additional_preperations = [line.rstrip() for line in lines] 
  
  with open(additional_ingredients_file_path) as file:
     lines = file.readlines()
     list_of_additional_ingredients = [line.rstrip() for line in lines] 
  
  with open(dairy_list_path) as file:
     lines = file.readlines()
     list_of_dairy_ingredients = [line.rstrip() for line in lines] 
  
  with open(fruit_list_path) as file:
     lines = file.readlines()
     list_of_fruit_ingredients = [line.rstrip() for line in lines]
     
  with open(grain_list_path) as file:
     lines = file.readlines()
     list_of_grain_ingredients = [line.rstrip() for line in lines]
  
  with open(nonveg_list_path) as file:
     lines = file.readlines()
     list_of_nonveg_ingredients = [line.rstrip() for line in lines]
  
  with open(nut_list_path) as file:
     lines = file.readlines()
     list_of_nut_ingredients = [line.rstrip() for line in lines]
  
  with open(pulses_list_path) as file:
     lines = file.readlines()
     list_of_pulses_ingredients = [line.rstrip() for line in lines]
  
  with open(spices_list_path) as file:
     lines = file.readlines()
     list_of_spices_ingredients = [line.rstrip() for line in lines]
  
  with open(veggie_list_path) as file:
     lines = file.readlines()
     list_of_veggie_ingredients = [line.rstrip() for line in lines]

  with open(herb_list_path) as file:
     lines = file.readlines()
     list_of_herb_ingredients = [line.rstrip() for line in lines]
  
  with open(sauce_list_path) as file:
     lines = file.readlines()
     list_of_sauce_ingredients = [line.rstrip() for line in lines]
  
  def preprocess(sent):
    sent = nltk.word_tokenize(sent)
    sent = nltk.pos_tag(sent)
    return sent
  
  for i in range(len(ingredients)):
    ingredients[i] = ingredients[i].replace('fat free','fat-free')
    tokens = preprocess(ingredients[i].lower())
    for token in tokens:
      if '®' in token[0]:
        continue
      elif token[0] in list_of_additional_descriptors:
        descriptor[i]+= token[0]+' '
      elif token[0] in list_of_additional_preperations:
        preparation[i]+= token[0]+' '
      elif token[0] in list_of_additional_ingredients:
        main_ingredients[i]+= token[0]+' '
      elif token[1] in ['JJ','JJR','JJS']:
        descriptor[i]+= token[0]+' '
      elif token[1] in ['VBN','VBD']:
        preparation[i]+= token[0]+' '
      elif token[1] in ['NN','NNS','NNP','NNPS']:
        main_ingredients[i] += token[0]+' '
    main_ingredients[i] = main_ingredients[i].rstrip()
    descriptor[i] = descriptor[i].rstrip()
    preparation[i] = preparation[i].rstrip()
  Ingredients = [0] * len(ingredients)
  for i in range(len(ingredients)):
    new_ingredient = Ingredient(fullname=ingredients[i],main_ingredients=main_ingredients[i],quantity_type=quantity_type[i],quantity = quantities[i],units=units[i],descriptor=','.join(descriptor[i].split()),preparation=','.join(preparation[i].split()))
    Ingredients[i] = new_ingredient
    
    for item in list_of_dairy_ingredients:
        if match_ingredient(item,new_ingredient):
            Ingredients[i].ingredient_type = 'Dairy'
            break
  
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_sauce_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Sauce/Dressing'
                break
    
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_grain_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Grain'
                break
   
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_nonveg_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Meat/Fish'
                break
   
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_fruit_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Fruit'
                break
    
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_nut_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Nut'
                break
    
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_grain_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Grain'
                break
    
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_pulses_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Pulses'
                break
    
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_spices_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Spice/Condiment'
                break
    
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_veggie_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Vegetable'
                break
    
    if (Ingredients[i].ingredient_type =='General'):
        for item in list_of_herb_ingredients:
            if match_ingredient(item,new_ingredient):
                Ingredients[i].ingredient_type = 'Herb'
                break
    
    
            
  for i in range(len(Ingredients)):
    step_indexes = []
    for j in range(len(directions)):
      direction_lower = directions[j]
      
      if 'all other ingredients' in direction_lower or 'all ingredients' in direction_lower or 'other ingredients' in direction_lower or 'remaining ingredients' in direction_lower and len(step_indexes)==0:
        step_indexes.append(j)    
        index  = re.search('all other ingredients except|all ingredients except',direction_lower).start()
        if check_ingredient(Ingredients[i].main_ingredients,direction_lower[index:]) or check_ingredient(Ingredients[i].main_ingredients.replace(" ", ""),direction_lower[index:]):
            step_indexes.remove(j)
      
      elif 'vegetables' in direction_lower.split() in direction_lower and len(step_indexes)==0 and Ingredients.ingredient_type=='Vegetable':
        step_indexes.append(j) 
      
      elif 'fruits' in direction_lower.split() and len(step_indexes)==0 and Ingredients.ingredient_type=='Fruit':
        step_indexes.append(j)  
      
      elif 'grains' in direction_lower.split() and len(step_indexes)==0 and Ingredients.ingredient_type=='Grain':
        step_indexes.append(j) 
      
      elif 'nuts' in direction_lower.split() and len(step_indexes)==0 and Ingredients.ingredient_type=='Nut':
        step_indexes.append(j)
        
      elif 'spices' in direction_lower.split() and len(step_indexes)==0 and Ingredients.ingredient_type=='Spice/Condiment':
        step_indexes.append(j)
        
      elif check_ingredient(Ingredients[i].main_ingredients,direction_lower) or check_ingredient(Ingredients[i].main_ingredients.replace(" ", ""),direction_lower):
        step_indexes.append(j)

      
    Ingredients[i].step_indexes = step_indexes
  
  myRecipie.Ingredients = Ingredients
  #----------------------------Ingredients are ready---------------------------#
  
  #----------------------------Parsing Tools-----------------------------------#
  with open(tools_path) as file:
      lines = file.readlines()
      list_of_tools = [line.rstrip() for line in lines]
  
  df_tools = pd.read_csv(implied_tools_path)
  df_tools = df_tools.to_numpy()
  
  Tools = []
  for i in range(len(directions)):
    direction_lower = directions[i]
    for tool in list_of_tools:
      if tool in direction_lower or singularize(tool) in direction_lower or pluralize(tool) in direction_lower:
        if tool not in Tools:
            Tools.append(tool.strip())
    for keyword,implied_tool in df_tools:
      if keyword.lower() in direction_lower and implied_tool not in Tools:
        Tools.append(implied_tool.strip())

  myRecipie.Tools = Tools
  #----------------------------Tools are ready--------------------------#

  #----------------------------Parsing Methods--------------------------#
  Cooking_Methods = []
  with open(cooking_method_path) as file:
      lines = file.readlines()
      list_of_cooking_methods = [line.rstrip() for line in lines]
  
  lemmatizer = WordNetLemmatizer()
  for i in range(len(directions)):
    direction_lower = directions[i].lower().split()
    for cooking_method in list_of_cooking_methods:
      if cooking_method in direction_lower or lemmatizer.lemmatize(cooking_method) in direction_lower or singularize(cooking_method) in direction_lower or pluralize(cooking_method) in direction_lower:
        if cooking_method not in Cooking_Methods:
            Cooking_Methods.append(cooking_method.strip())
      if cooking_method in title_text or lemmatizer.lemmatize(cooking_method) in title_text:
        myRecipie.primary_cooking_method =  cooking_method
        
  if (myRecipie.primary_cooking_method == None ) and len(Cooking_Methods)!=0:
    myRecipie.primary_cooking_method = Cooking_Methods[0]
  myRecipie.Methods = Cooking_Methods
  #----------------------------Methods are ready--------------------------#

  #----------------------------Parsing Directions--------------------------#
  Steps = []

  for i in range(len(directions)):
    direction_lower = directions[i].lower()
    step_wise_ingredients = []
    step_wise_tools = []
    step_wise_methods = []
    step_wise_times = ''
    
    for tool in Tools:
      if tool in direction_lower and tool not in step_wise_tools:
        step_wise_tools.append(tool.strip())
      for keyword,implied_tool in df_tools:
        if keyword.lower() in direction_lower and implied_tool not in step_wise_tools:
            step_wise_tools.append(implied_tool.strip())
    
    for method in Cooking_Methods:
      if method in direction_lower and method not in step_wise_methods:
        step_wise_methods.append(method.strip())
    
    for ingredient in Ingredients:
        for index in ingredient.step_indexes:
            if index==i:
                step_wise_ingredients.append(ingredient)
    
    time_keywords = ' minutes| seconds| hours| secs| hrs| mins| min'
    if (re.search(time_keywords,direction_lower)):
      index = re.search(time_keywords,direction_lower).start()
      new_str = direction_lower[:index]
      step_wise_times+= str(new_str.split()[-1])
      unit = re.findall(time_keywords,direction_lower)[0]
      step_wise_times += ''+str(unit)
      direction_lower_split = direction_lower.split()
      for j in range(1,len(direction_lower_split)-1):
        if direction_lower_split[j] == 'to' and direction_lower_split[j-1].isnumeric() and direction_lower_split[j+1].isnumeric():
            step_wise_times = direction_lower_split[j-1]+' to '+step_wise_times
      
    new_step = Step (full_step=directions[i],ingredients=step_wise_ingredients,tools=step_wise_tools,methods = step_wise_methods,times=step_wise_times,index=i)
    Steps.append(new_step)
  myRecipie.Steps = Steps

    
  return myRecipie
 #----------------------------Directions are ready--------------------------#

def check_ingredient(ingredient,step):
  if ingredient.lower() in ['baking powder','baking soda']:
    if ingredient.lower() in step.lower() or pluralize(ingredient.lower()) in step.lower() or singularize(ingredient.lower()) in step.lower():
        return True
  elif len(ingredient.split())==1:
    if ingredient.lower() in step.lower() or pluralize(ingredient.lower()) in step.lower() or singularize(ingredient.lower()) in step.lower():
      return True
  else:
    matches = 0
    for word in ingredient.split():
      if word.lower() in step.lower() or pluralize(word.lower()) in step.lower() or singularize(word.lower()) in step.lower():
        matches+=1
    if len(ingredient.split())==2:
      if matches>=1:
        return True
    elif len(ingredient.split())-matches <= 2:
        return True
  return False

def tokenize_and_sub(stri,ingredient,new_ingredient):

  tokenizer = RegexpTokenizer(r'\w+')
  token = tokenizer.tokenize(ingredient)
  for i in range(len(ingredient.split()),0,-1):
    ngram = list(ngrams(token, i))
    substrings = []  
    for j in range(len(ngram)):
      substrings.append(' '.join(ngram[j]))
    for substring in substrings:
      if substring in stri:
        stri = stri.replace(substring,new_ingredient)
        return stri
  return stri


'''
def match_ingredient(keyword,Ingredient):
    main_ingredients_words = Ingredient.main_ingredients.lower().split()
    full_ingredient_words = Ingredient.fullname.lower().split()
    keyword_lower = keyword.lower()
    if keyword in main_ingredients_words or keyword in full_ingredient_words:
        return True
    
    if singularize(keyword) in main_ingredients_words or singularize(keyword) in full_ingredient_words:
        return True
    
    if pluralize(keyword) in main_ingredients_words or pluralize(keyword) in full_ingredient_words:
        return True
    return False
'''
'''
def match_ingredient(keyword,Ingredient):
    main_ingredients_words = Ingredient.main_ingredients.lower()
    full_ingredient_words = Ingredient.fullname.lower()
    keyword_lower = keyword.lower()
    if keyword in main_ingredients_words or keyword in full_ingredient_words:
        return True
    
    if singularize(keyword) in main_ingredients_words or singularize(keyword) in full_ingredient_words:
        return True
    
    if pluralize(keyword) in main_ingredients_words or pluralize(keyword) in full_ingredient_words:
        return True
    return False
'''
def match_ingredient(keyword,Ingredient):
    main_ingredients_words = Ingredient.main_ingredients.lower()
    full_ingredient_words = Ingredient.fullname.lower()
    keyword_lower = keyword.lower()
    if keyword in main_ingredients_words:
        return True
    
    if singularize(keyword) in main_ingredients_words:
        return True
    
    if pluralize(keyword) in main_ingredients_words:
        return True
    return False
    
def fix_fraction(stri):
    def frac2string(s):
        i, f = s.groups(0)
        f = Fraction(f)
        return str(int(i) + float(f))
    
    return re.sub(r'(?:(\d+)[-\s])?(\d+/\d+)', frac2string, stri)
    

def print_choices():
    print('1. Parse and display a new recipie')
    print('2. Ratio the ingredients of current recipie')
    print('3. Convert current recipie to vegeterian')
    print('4. Convert current recipie to gluten free')
    print('5. Convert current recipie to indian')
    print('6. Convert current recipie to chinese')
    print('7. Convert current recipie to a cheaper alternative')
    print('8. Convert current recipie to a healthier alternative')
    print('0. Exit')

print('Welcome to Interactive Cook Book')   
print('Please run this program in powershell and fully maximized for an optimum viewing experience')
choice = -100
url_choice = 0
myRecipie = None
check = False
while (True):
    
    print('Please enter a choice')
    print_choices()
    
    choice = input()
    
    if choice.isnumeric():
        choice = int(choice)
    else:
        print('Invalid Choice!')
        continue
    
    if choice not in (0,1) and not myRecipie:
        print('You havent selected a recipie yet!')
        continue
        
    if choice==0:
        print('Bye!')
        break
    
    elif choice==1:
        #print('Will you give a url, or shall I just take any random recipe?')
        #print('Press 1 to enter url or 2 to randomly select')
        #url_choice = int(input())
        url_choice = 1
        if url_choice == 1:
            print('Press enter url: ',end='')
            input_url = input()
            input_url = input_url.strip()
            try:
                myRecipie = get_recipie_from_URL(input_url)
                myRecipie.print_recipie()
            except:
                print('Connection error please try again')
        elif url_choice == 2:
            random_URL ="http://allrecipes.com/recipe/" + str(random.randint(6660, 27000))
            myRecipie = get_recipie_from_URL(random_URL)
            myRecipie.print_recipie()
        else:
            print('Invalid choice')
    
    elif choice==2:
        print('Enter a ratio to multiply the recipie by')
        print('For example, 2 will double the ingredients and 0.5 will divide the ingredients by 2')
        input_ratio = float(input())
        myRecipie.ratio(input_ratio)
        myRecipie.print_recipie()
    
    elif choice==3:
        check = myRecipie.to_veg()
        if check:
            myRecipie.print_recipie()
    
    elif choice==4:
        check = myRecipie.to_gluten_free()
        if check:
            myRecipie.print_recipie()
    
    elif choice==5:
        check = myRecipie.to_indian()
        if check:
            myRecipie.print_recipie()
    
    elif choice==6:
        check = myRecipie.to_chinese()
        if check:
            myRecipie.print_recipie()
    
    elif choice==7:
        check = myRecipie.to_cheap()
        if check:
            myRecipie.print_recipie()
    
    elif choice==8:
        check = myRecipie.to_healthy()
        if check:
            myRecipie.print_recipie()
    
    else:
        print('Invalid choice')