import requests
import re
import os
from bs4 import BeautifulSoup
import hashlib
import json

product = {
  "id": "",
  "handle": "",
  "name": "",
  "category": "",
  "price": "",
  "compare_at_price": "",
  "sku": "",
  "description": "",
  "images": [],
  "in_stock": "a",
}

def reset_product():
  global product
  product = {
    "id": "",
    "handle": "",
    "name": "",
    "category": "",
    "price": "",
    "compare_at_price": None,
    "sku": "",
    "description": "",
    "images": [],
    "in_stock": "",
  }

def open_link_list(filepath):
  with open("products.json", 'w') as f:
    f.write("[\n")

  link_list = get_link_list_from_file(filepath)
  for link in link_list:
    reset_product()
    url = link.strip()
    soup = get_soup_from_url(url)
    if not soup:
      # log failed links
      with open("failed.txt", 'a') as f:
        f.write(f"{url}\n")
      continue
    nodes = get_nodes_from_soup(soup, "thumb-item")
    path_handle = url.split("/")[-1].split(".")[0]
    path_b = re.search(r"p\d+", path_handle)
    if path_b:
      path_b = path_b.group()
      path_handle = path_handle.replace("-" + path_b, "")
    if nodes:
      save_img_from_nodes(nodes, path_handle)
    product["id"] = path_b.replace("p", "")
    product["handle"] = path_handle
    product["name"] = soup.find(class_="title").text.strip()
    product["category"] = soup.find_all(class_="breadcrumb-item")[1].find("a")["href"].split("/")[-2]
    button_atc = soup.find(class_="btn btn-add-to-cart")
    if button_atc:
      product["in_stock"] = "999"
    else:
      product["in_stock"] = "0"
    display_price = soup.find(class_="price").text.strip() # 1.000.000đ / Bình (giá + đơn vị tính)
    # convert price to number
    product["price"] = display_price.split("đ")[0].replace(".", "")
    product["sku"] = soup.find(itemprop="sku").text.strip()
    product["description"] = soup.find(class_="product-feture").encode_contents().decode("utf-8")
    print(f"Product #{product['id']} {product['name']} crawled.")
    # save product to file json
    save_product_to_json(product, "products.json")
    # add a comma to separate products
    with open("products.json", 'a') as f:
      f.write(",\n")

  # when done, add a closing bracket to the file
  with open("products.json", 'a') as f:
    f.write("]")

def save_product_to_json(product, filepath):
  with open(filepath, 'a', encoding="utf-8") as f:
    f.write(json.dumps(product, ensure_ascii=False))

def get_link_list_from_file(filepath):
  with open(filepath, 'r') as f:
    link_list = f.readlines()
  return link_list

def hash_img_name(img_name, length):
  # Run sha256 on img_name and return the first length characters
  ext = img_name.split('.')[-1]
  if len(ext) > 5:
    ext = "jpg"
  return hashlib.sha256(img_name.encode()).hexdigest()[:length] + '.' + ext

def get_soup_from_url(url):
  response = requests.get(url)
  if response.status_code == 200:
    return BeautifulSoup(response.content, 'html.parser')
  else:
    print("Failed to retrieve HTML.")
    return None

def get_nodes_from_soup(soup, class_list):
    nodes = soup.find_all(class_=class_list)
    if nodes:
      # print(nodes)
      return nodes
    else:
      print("Node not found.")
      return None

def save_img_from_nodes(nodes, filepath):
  for node in nodes:
    img_url = node.find('img')['src']
    img_name = hash_img_name(img_url.split('/')[-1], 10)
    img_response = requests.get(img_url)

    if not os.path.exists(filepath):
      os.makedirs(filepath)

    if img_response.status_code == 200:
      with open(f"{filepath}/{img_name}", 'wb') as f:
        f.write(img_response.content)
        print(f"Saved {filepath}/{img_name}")
        product["images"].append(img_name)
    else:
      print(f"Failed to retrieve image {img_name}")
      # create a file to log failed images
      with open(f"{filepath}/failed.txt", 'a') as f:
        f.write(f"{img_url}\n")

# Example usage
# url = "https://shop.dalathasfarm.com/a7/ke-hoa-chuc-mung-004-p11.html"
# class_list = "thumb-item"
# nodes = get_node_from_url(url, class_list)
# path_handle = url.split("/")[-1].split(".")[0]
# if nodes:
  # save_img_from_nodes(nodes, path_handle)
# print(get_nodes_from_url("https://shop.dalathasfarm.com/a7/ke-hoa-chuc-mung-004-p11.html", "breadcrumb-item")[1].find("a")["href"].split("/")[-2])

open_link_list("links_wip.csv")

def remove_duplicate_links_in_csv(filepath):
  with open(filepath, 'r') as f:
    link_list = f.readlines()
  link_list = list(set(link_list))
  with open("a" + filepath, 'w') as f:
    for link in link_list:
      f.write(link)

# remove_duplicate_links_in_csv("links.csv")