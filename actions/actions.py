# This files contains your custom actions which can be used to run
# custom Python code.
#
# See this guide on how to implement these action:
# https://rasa.com/docs/rasa/custom-actions


# This is a simple example for a custom action which utters "Hello World!"
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
from beautifultable import BeautifulTable
from pattern.en import pluralize, singularize
from nltk.util import ngrams
from nltk.tokenize import RegexpTokenizer
from fractions import Fraction

main_path = "data/"
extra_path = "extra/"
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

subs_path = 'substitutes.csv'

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
  
  def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, 
            sort_keys=True, indent=4)
            
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

  #----------------------------Directions are ready--------------------------#
  return myRecipie
 
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
    
from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import wikipedia
import json
from types import SimpleNamespace
from youtubesearchpython import VideosSearch
import wikipediaapi

class getYoutubeURL(Action):

     def name(self) -> Text:
         return "action_get_youtube_url"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

         text = tracker.latest_message['text']
         sentence = tracker.latest_message['text']
         text = text.lower().split()
            
         search_query = tracker.get_slot("object")
         
         if (search_query and 'how' in text):
            videosSearch = VideosSearch(search_query, limit = 2)
            title = videosSearch.result()['result'][0]['title']
            link= videosSearch.result()['result'][0]['link']
            message = 'Heres a youtube video: \'' + title + '\''
            dispatcher.utter_message(text = message)
            message = 'The Link is: ' + link
            dispatcher.utter_message(text = message)
            
         else:
            method_in_text = False
            tool_in_text = False
            ingredient_in_text = False
            search_query = ''
            
            myRecipe = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
            myStepNo = int(tracker.get_slot("step_no"))
            
          
            for method in myRecipe.Steps[myStepNo].methods:
                if method in text or method in sentence:
                    search_query.append+=method
                    method_in_text = True
            
            for ingredient in myRecipe.Ingredients:
                if ingredient.main_ingredients.split()[0] in text or ingredient.main_ingredients in sentence:
                    search_query+=ingredient.main_ingredients
                    ingredient_in_text = True
                    
            for tool in myRecipe.Steps[myStepNo].tools:
                if tool in text or tool in sentence:
                    search_query+=tool
                    tool_in_text = True
            
            if search_query == '':
                if len(myRecipe.Steps[myStepNo].methods)>0:
                    search_query = myRecipe.Steps[myStepNo].methods[0]
            
            if search_query == '':
                dispatcher.utter_message(text="I am sorry I dont know what you are confused about")           
            
            if method_in_text:
                videosSearch = VideosSearch(search_query, limit = 2)
                title = videosSearch.result()['result'][0]['title']
                link= videosSearch.result()['result'][0]['link']
                message = 'Heres a youtube video: \'' + title + '\''
                dispatcher.utter_message(text = message)
                message = 'The Link is: ' + link
                dispatcher.utter_message(text = message)
             
            else:
                dispatcher.utter_message(text="Heres a wiki summary of"+search_query)
                #title = wikipedia.search(search_query, results = 1,suggestion = True)
                #dispatcher.utter_message(text=wikipedia.summary(title,sentences =2))
                wiki_wiki = wikipediaapi.Wikipedia('en')
                page_py = wiki_wiki.page(search_query)
                dispatcher.utter_message(text=page_py.summary)
                #dispatcher.utter_message(text='Heres the url:'+page_py.url)
         return []

'''class getWikipediaSummary(Action):

     def name(self) -> Text:
         return "action_get_wikipedia_summary"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

         search_query = tracker.get_slot("object")
         
         if (search_query):
            dispatcher.utter_message(text="Let me look up "+search_query)
            dispatcher.utter_message(text=wikipedia.summary(search_query))
         else:
            dispatcher.utter_message(text="I could not find your search query")
         return []
'''

class getRecipie(Action):

     def name(self) -> Text:
         return "action_get_recipie_from_url"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         
         url = tracker.latest_message['text']
         recipie = get_recipie_from_URL(url)
         dispatcher.utter_message(text="Loaded Recipe. What do you want do first?")
         serialized = recipie.toJSON()
         getRecipeObjectFromJSON(serialized).print_recipie()
         return [SlotSet("recipie",serialized),SlotSet("step_no",-1)]
         
class getIngredients(Action):

     def name(self) -> Text:
         return "action_get_ingredient_list"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         myrecipie = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
         ingredient_list = []
         for ingredient in myrecipie.Ingredients:
            row = [ingredient.fullname,str(ingredient.quantity) +' '+ ingredient.units]
            dispatcher.utter_message(text=','.join(row))
         '''
         for ingredient in recipie.Ingredients:
            ingredient_list.append(ingredient.fullname)
         dispatcher.utter_message(text=(','.join(ingredient_list)))
         '''
         
         return []

class getNextStep(Action):

     def name(self) -> Text:
         return "action_get_next_step"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         myRecipe = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
         myStepNo = int(tracker.get_slot("step_no"))
         skipahead = 1
         numbers = ['one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen']
         text = tracker.latest_message['text']
         text = text.lower().split()
         for i in range(0,len(numbers)):
            if (numbers[i] in text):
                skipahead = i+1
                break         
         if myStepNo + skipahead >= len(myRecipe.Steps):
            dispatcher.utter_message(text='There are only '+str(len(myRecipe.Steps))+' steps in the recipe')
            return []
         else:
            step = myRecipe.Steps[myStepNo+skipahead].full_step
            step = str(myStepNo+skipahead+1) +" : " + step
            dispatcher.utter_message(text=step)
            return [SlotSet("step_no",myStepNo+skipahead)]

class getPreviousStep(Action):

     def name(self) -> Text:
         return "action_get_previous_step"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         myRecipe = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
         myStepNo = int(tracker.get_slot("step_no"))
         skipback = 1
         numbers = ['one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen']
         text = tracker.latest_message['text']
         text = text.lower().split()
         for i in range(0,len(numbers)):
            if (numbers[i] in text):
                skipback = i+1
                break         
         if myStepNo - skipback < 0:
            dispatcher.utter_message(text='You cant go back that many steps')
            return []
         else:
            step = myRecipe.Steps[myStepNo-skipback].full_step
            step = str(myStepNo-skipback+1) +" : " + step
            dispatcher.utter_message(text=step)
            return [SlotSet("step_no",myStepNo-skipback)]

class repeatLastMessage(Action):

     def name(self) -> Text:
         return "action_repeat_previous_message"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         message = next(e for e in reversed(tracker.events) if e["event"] == "bot").get('text')
         dispatcher.utter_message(text="okay, I'll repeat: "+str(message))
         return []
         
class getNStep(Action):

     def name(self) -> Text:
         return "action_give_n_step"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         myRecipe = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
         myStepNo = int(tracker.get_slot("step_no"))
         newStep = None
         text = tracker.latest_message['text']
         text = text.lower().split()
         ordinal_numbers_spelt = ['1st','2nd','3rd','4th','5th','6th','7th','8th','9th','10th','11th','12th','13th','14th','15th','16th','17th']
         ordinal_numbers = ['first','second','third','fourth','fifth','sixth','seventh','eighth','ninth','tenth','eleventh','twelfth','thirteenth','fourteenth','fifteenth','sixteenth','seventeenth']
         numbers = ['one','two','three','four','five','six','seven','eight','nine','ten','eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen']
         digits = ['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17']
         for i in range(0,len(ordinal_numbers)):
            if (ordinal_numbers_spelt[i] in text or ordinal_numbers[i] in text or numbers[i] in text or digits[i] in text):
                newStep = i
                break
         if newStep == None and 'last' in text:
            newStep = len(myRecipe.Steps)-1
         if newStep==None:
            message = 'I did not understand which step you wanted to go to, perhaps you are making a typo'
            dispatcher.utter_message(text=message)
            return []
         else:
            if newStep > (len(myRecipe.Steps)-1):
                dispatcher.utter_message(text='There are only '+str(len(myRecipe.Steps))+' steps in the recipe')
                return []
            else:
                step = myRecipe.Steps[newStep].full_step
                step = str(newStep+1) +" : " + step
                dispatcher.utter_message(text=step)
                return [SlotSet("step_no",newStep)]

class getIngredientAmount(Action):

     def name(self) -> Text:
         return "action_give_ingredient_amount"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         myRecipie = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
         myStepNo = int(tracker.get_slot("step_no"))
         no_ingredient_found_in_query = True
         text = tracker.latest_message['text']
         sentence = tracker.latest_message['text']
         text = text.lower().split()
         
         for ingredient in myRecipie.Ingredients:
            if check_ingredient(ingredient.fullname,sentence) or check_ingredient(ingredient.main_ingredients,sentence):
                dispatcher.utter_message(text=(str(ingredient.quantity)+" "+ingredient.units))
                no_ingredient_found_in_query = False
                return []
         
         message = []
         if (no_ingredient_found_in_query):
            for ingredient in myRecipie.Ingredients:
                if myStepNo in ingredient.step_indexes:
                    message.append(ingredient.main_ingredients+" : "+ str(ingredient.quantity) +" "+ingredient.units)
         dispatcher.utter_message(text=(','.join(message)))
         return []

class getTime(Action):

     def name(self) -> Text:
         return "action_give_time"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         myRecipie = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
         myStepNo = int(tracker.get_slot("step_no"))
         dispatcher.utter_message(text=myRecipie.Steps[myStepNo].times)
         return []

class getTemperature(Action):

     def name(self) -> Text:
         return "action_give_temperature"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         myRecipe = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
         myStepNo = int(tracker.get_slot("step_no"))
         step = myRecipe.Steps[myStepNo].full_step
         found = re.search('degrees F',step)
         if found == None:
            found = re.search('degree F',step)
         if found!=None:
            new_str = step[:found.start()]
            temp_val = new_str.split()[-1]
            temp_unit = 'degrees F'
         else:
            found = re.search('degrees C',step)
            if found==None:
                found = re.search('degree C',step)
            if found!=None:
                new_str = step[:found.start()]
                temp_val = new_str.split()[-1]
                temp_unit = 'degrees C'
         if found==None:
            dispatcher.utter_message(text='Sorry not found any temperature data')
         else:
            dispatcher.utter_message(text=temp_val +' '+temp_unit)
         return []

class getIngredientSubstitute(Action):

     def name(self) -> Text:
         return "action_give_ingredient_sub"

     def run(self, dispatcher: CollectingDispatcher,
             tracker: Tracker,
             domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
         myRecipie = getRecipeObjectFromJSON(tracker.get_slot("recipie"))
         myStepNo = int(tracker.get_slot("step_no"))
         no_ingredient_found_in_query = True
         no_substitute_found_in_csv = True
         text = tracker.latest_message['text']
         sentence = tracker.latest_message['text']
         text = text.lower().split()
         df_ingredients = pd.read_csv(subs_path)
         df_ingredients = df_ingredients.to_numpy()
         
         for ingredient in myRecipie.Ingredients:
            if check_ingredient(ingredient.fullname,sentence) or check_ingredient(ingredient.main_ingredients,sentence):
                no_ingredient_found_in_query = False
                for item,substitute_ingredient in df_ingredients:
                    if match_ingredient(item,ingredient):
                        dispatcher.utter_message(text='You can use '+substitute_ingredient+' instead')
                        no_substitute_found_in_csv = False
                        return []
                if (no_substitute_found_in_csv):
                    dispatcher.utter_message(text='Sorry, I dont have a substituiton for '+ingredient.main_ingredients+' in my database')
                    return []
                  
         if (no_ingredient_found_in_query):
                  dispatcher.utter_message(text='I could not understand what ingredient you needed a substituiton for')
         return []

def getRecipeObjectFromJSON(serialized):
    json_data = json.loads(serialized, object_hook=lambda d: SimpleNamespace(**d))
    myRecipie = Recipe()
    myRecipie.Tools = json_data.Tools
    myRecipie.Methods = json_data.Methods
    myRecipie.Ingredients = []
    myRecipie.Steps = []
    for i in range(len(json_data.Ingredients)):
        myIngredient = Ingredient()
        myIngredient.fullname = json_data.Ingredients[i].fullname
        myIngredient.main_ingredients = json_data.Ingredients[i].main_ingredients
        myIngredient.quantity_type = json_data.Ingredients[i].quantity_type
        myIngredient.quantity = json_data.Ingredients[i].quantity
        myIngredient.units = json_data.Ingredients[i].units
        myIngredient.descriptor = json_data.Ingredients[i].descriptor
        myIngredient.preparation = json_data.Ingredients[i].preparation
        myIngredient.step_indexes = json_data.Ingredients[i].step_indexes
        myIngredient.ingredient_type= json_data.Ingredients[i].ingredient_type
        myRecipie.Ingredients.append(myIngredient)
             
    for i in range(len(json_data.Steps)):
        myStep = Step()
        myStep.full_step = json_data.Steps[i].full_step
        myStep.ingredients = []
        myStep.tools = json_data.Steps[i].tools
        myStep.methods = json_data.Steps[i].methods
        myStep.times = json_data.Steps[i].times
        myStep.index = json_data.Steps[i].index
        for ingredient in myRecipie.Ingredients:
            for index in ingredient.step_indexes:
                if index==i:
                    myStep.ingredients.append(ingredient)
        myRecipie.Steps.append(myStep)
    
    return myRecipie