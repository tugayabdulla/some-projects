import os
import sys
import time

from pcloud import PyCloud
from requests_html import AsyncHTMLSession
from requests import get

asession = AsyncHTMLSession()
headers = {
    'Authorization': 'API-Key Cph30qkLrdJDkjW-THCeyA',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:87.0) Gecko/20100101 Firefox/87.0',
    'accept': 'application/json, text/plain, */*',
    'accept-encoding': 'gzip, deflate, br'
}
url = 'https://api.generated.photos/api/frontend/v1/images?order_by=oldest&page={}&per_page=100&face=natural&head_pose=right-facing'
id_url = 'https://api.generated.photos/api/frontend/v1/images/{}'
structured_upload_url = 'https://eapi.pcloud.com/uploadfile'
total_upload_url = 'https://api.pcloud.com/uploadfile'

print(f'There are {get(url.format(1), headers=headers).json()["total"]} images totally')

email = 'mikevinitsky@gmail.com'
password = 'zxcvbnm11'
pc_structured = PyCloud(email, password, endpoint="eapi", token_expire=1000000000)
token_structured = pc_structured.auth_token

email = 'mmv123@mail.com'
password = 'zxcvbnm11'
pc_total = PyCloud(email, password, endpoint="api", token_expire=1000000000)
token_total = pc_total.auth_token

with open('done1.txt', 'r') as f:
    done = f.readlines()

total = get(url.format(1), headers=headers).json()["total"]
print(f'There are {total} images in this category totally')

done = [i[:-1] for i in done]
done = set(done)
print(f'There are {len(done)} images processesd')


def download_image(id):
    global data_dictionary

    async def download():
        img_url = data_dictionary[id][1]
        while True:

            try:
                r = await asession.get(img_url)
                break
            except:
                pass
        with open(f'{id}.png', 'wb') as f:
            f.write(r.content)

    return download


def get_image_ids(i):
    global img_ids

    async def parse():
        while True:
            try:
                r = await asession.get(url.format(i), headers=headers)
                break
            except Exception as e:
                pass
        images = r.json()['images']
        for image in images:
            id = image['id']
            if id not in done:
                img_ids.add(id)

    return parse


def get_image_url(id):
    global data_dictionary

    async def parse():
        while True:
            try:
                r = await asession.get(id_url.format(id), headers=headers)
                break
            except Exception as e:
                pass
        image = r.json()
        if 'meta' in image:
            meta = image['meta']
            path = f"/Images/Natural/Right Facing/{meta['gender'][0]}/{meta['age'][0]}/{meta['ethnicity'][0]}/{meta['eye_color'][0]}/{meta['hair_color'][0]}/{meta['hair_length'][0]}/{meta['emotion'][0]}"
            img_url = image['transparent']['thumb_url']
            data_dictionary[id] = (path, img_url)
        else:
            img_ids.remove(id)

    return parse


def upload(id):
    global data_dictionary

    async def post():
        files = [("file", open(f'{id}.png', "rb"))]
        params = {'path': data_dictionary[id][0], 'auth': token_structured}
        req = await asession.post(structured_upload_url, data=params, files=files)
        while req.status_code != 200:
            req = await asession.post(structured_upload_url, data=params, files=files)

        params = {'path': '/All images', 'auth': token_total}
        files = [("file", open(f'{id}.png', "rb"))]
        req = await asession.post(total_upload_url, data=params, files=files)
        while req.status_code != 200:
            req = await asession.post(total_upload_url, data=params, files=files)
        done.add(id)
        os.remove(f'{id}.png')

    return post


try:
    for _ in range(2):
        for j in range(0, total // 500 + 2):
            start = time.time()
            img_ids = set()
            # getting image ids
            try:
                asession.run(*[get_image_ids(i) for i in range(j * 5 + 1, (j + 1) * 5 + 1)])
            except Exception as e:
                continue
            data_dictionary = {}
            # getting image urls
            try:
                if len(img_ids) != 0:
                    asession.run(*[get_image_url(id) for id in img_ids])
                    if len(img_ids) != 0:
                        # downloading images
                        asession.run(*[download_image(id) for id in data_dictionary])
                        # uploading to pcloud
                        asession.run(*[upload(id) for id in data_dictionary])
            except Exception as e:
                continue
            end = time.time()

            with open('done1.txt', 'a') as f:
                for id in list(img_ids):
                    f.write(str(id) + '\n')
        url = 'https://api.generated.photos/api/frontend/v1/images?order_by=recent&page={}&per_page=100&face=natural&head_pose=right-facing'


except Exception as e:
    sys.exit()
