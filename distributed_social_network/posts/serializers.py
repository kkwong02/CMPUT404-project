import io
import random


from requests.auth import HTTPBasicAuth
from rest_framework.parsers import JSONParser
from rest_framework import serializers

from posts.models import Post, Categories, Comment
from users.models import User
import requests

visilibityDict = {
    "public": "PUBL",
    'friend of a friend': "FOAF",
    'private': "PRIV",
    'friends': 'FRND'
}
contentTypeDict={
    "text/markdown":"MKD",
    "text/plain":"TXT",
    "application/base64":"APP",
    "image/png;base64":"PNG",
    "image/jpeg;base64":"JPG"
}


def friend_checking(a):
    stream = io.BytesIO(a.content)
    data = JSONParser().parse(stream)
    l = friend_check_serializer(data=data)
    if l.is_valid():
        return l.validated_data['friends']
    else:
        return False

async def requestPosts(node, ending, current_id):
    try:
        a = requests.get(node.hostname+node.prefix+ending, headers={"X-User":str(current_id)}, auth=HTTPBasicAuth(node.send_username,node.send_password))

        if a.status_code!=200:
            print(a.status_code)
            print('pepega')
            a = requests.get(node.hostname + node.prefix + ending, headers={"X-AUTHOR-ID": str(current_id)},
                             auth=HTTPBasicAuth(node.send_username, node.send_password))

        if a.status_code==200:
            print(a.elapsed.total_seconds())
            print('200')

            stream = io.BytesIO(a.content)
            data = JSONParser().parse(stream)
            l = posts_request_deserializer(data=data)
            l.is_valid()
            for i in l.validated_data['posts']:
                post = post_deserializer_no_comment(data=i)
                if post.is_valid():
                    if node.hostname in post.validated_data["origin"] or post.validated_data["origin"]=="":
                        new_post = post.create(post.validated_data)
                        if new_post!=None:
                            if new_post.origin=='':
                                new_post.origin = node.hostname+node.prefix+ 'posts/'+ str(new_post.id)

                            if new_post.source=='':
                                new_post.source = node.hostname+node.prefix+ 'posts/'+ str(new_post.id)

                            print('my host is:'+node.hostname)
                            new_post.author.host = node
                            new_post.author.save()
                            print(new_post.author.host.hostname)
                            new_post.save()
                            print('saved new post id :'+str(new_post.id))
                        else:
                            print('passed')
                            return True
                    else:
                        print(post.validated_data['origin'])
                        print(node.hostname)
                else:
                    print(post.errors)
            if l.validated_data['next']==None or l.validated_data['next']=='':
                return True
            else:
                print('going next')
                ending = l.validated_data['next'].split('/')[-1]
                result = await requestPosts(node, ending, current_id)
                return True

        else:
            print(node.hostname + node.prefix + ending)
            print(a.status_code)
    except Exception as e:
        print()
        print(e)

def requestSinglePost(link, current_id, node):
    try:
        print('getting:'+link)
        a = requests.get(link, headers={"X-User":str(current_id)}, auth=HTTPBasicAuth(node.send_username,node.send_password))
        if a.status_code!=200:
            print(a.status_code)
            a = requests.get(link, headers={"X-AUTHOR-ID":str(current_id)},auth=HTTPBasicAuth(node.send_username, node.send_password))
        if a.status_code==200:
            print('200')
            stream = io.BytesIO(a.content)
            data = JSONParser().parse(stream)
            l = posts_request_deserializer(data=data)
            if l.is_valid():
                print(l.validated_data)
                for i in l.validated_data['posts']:
            #assumes we have the post alrdy
                    post = post_detail_deserializer(data=i)
                    if post.is_valid():
                        post.create(post.validated_data)
                return True
            else:
                if len(l.errors.keys())==1 and 'posts' in l.errors.keys():
                    post = post_detail_deserializer(data=data)
                    if post.is_valid():
                        post.create(post.validated_data)
                    return True
                else:
                    print(l.data)
    except Exception as e:
        print('ERROR :',e)



def request_single_user(node,user, current_id):
    a=requests.get(user.get_url(),headers={"X-User":str(current_id)}, auth=HTTPBasicAuth(node.send_username,node.send_password))
    # print( a.status_code)
    if a.status_code!=200:
        a = requests.get(user.get_url(), headers={"X-AUTHOR-ID": str(current_id)},
                         auth=HTTPBasicAuth(node.send_username, node.send_password))
    if a.status_code==200:
        stream = io.BytesIO(a.content)
        data = JSONParser().parse(stream)
        deserialized=user_deserializer(data = data)
        if deserialized.is_valid():
            user.github=deserialized.validated_data['github']
            user.bio=deserialized.validated_data['bio']
            user.email = deserialized.validated_data['email']
            user.first_name=deserialized.validated_data['firstName']
            user.last_name=deserialized.validated_data['lastName']
            print('done')
        else:
            print(deserialized.errors)

    else:
        print(a.status_code)
        print('its boom')



class friend_check_serializer(serializers.Serializer):
    friends=serializers.BooleanField()


class user_detail_deserializer(serializers.Serializer):
    id = serializers.CharField()
    github = serializers.CharField(required=False, allow_blank=True, default='')
    bio = serializers.CharField(required=False, allow_blank=True, default='')
    email = serializers.CharField(required=False, allow_blank=True, default='')
    firstName = serializers.CharField(required=False, allow_blank=True, default='')
    lastName = serializers.CharField(required=False, allow_blank=True, default='')




# for multiple posts that you don't need the comments
class posts_request_deserializer(serializers.Serializer):
    posts = serializers.ListField()
    next = serializers.CharField(required=False,allow_blank=True,allow_null=True)



class post_detail_deserializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    source = serializers.CharField(required=False, default='')
    origin = serializers.CharField(required=False, default='')
    description = serializers.CharField(required=False, allow_blank=True)
    contentType = serializers.CharField()
    content = serializers.CharField(allow_blank=True)
    categories = serializers.ListField(required=False, default=[])
    published = serializers.DateTimeField()
    visibility = serializers.CharField()
    visibleTo = serializers.ListField(required=False, default=[])
    unlisted = serializers.BooleanField(required=False, default=False),
    comments = serializers.ListField()

    def create(self,validated_data):
        print(validated_data)
        existing_post=Post.objects.filter(id=validated_data['id'])
        existing_post.update(title=validated_data['title'],
                             content_type=contentTypeDict[validated_data['contentType']],
                             description=validated_data['description'],
                             content=validated_data['content'],)
                             #unlisted=validated_data['unlisted'])
        for comment in validated_data['comments']:
            a=comment_deserializer(data=comment)
            if a.is_valid():
                the_comment=a.create(a.validated_data,existing_post)
                if the_comment:
                    the_comment.save()
            else:
                print(a.errors)
        return True



class comment_deserializer(serializers.Serializer):
    contentType=serializers.CharField()
    comment=serializers.CharField()
    id=serializers.UUIDField()
    published=serializers.DateTimeField()
    author= serializers.DictField()

    def create(self,validated_data, comment_post):
        usr=user_deserializer(data=validated_data['author'])
        if usr.is_valid():
            comment_usr=usr.create(usr.validated_data)
            try:
                existing_comment=Comment.objects.get(id=validated_data['id'])
                return None
            except:
                return Comment.objects.create(
                    id=validated_data['id'],
                    comment=validated_data['comment'],
                    content_type=contentTypeDict[validated_data['contentType'].lower()],
                    author=comment_usr,
                    published=validated_data['published'],
                    post=comment_post[0]
            )



# for single post with no comments
class post_deserializer_no_comment(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    source = serializers.CharField(required=False, default='')
    description = serializers.CharField(required=False, allow_blank=True)
    contentType = serializers.CharField()
    author = serializers.DictField()
    content = serializers.CharField(allow_blank=True)
    categories = serializers.ListField(required=False, default=[])
    published = serializers.DateTimeField()
    visibility = serializers.CharField()
    visibleTo = serializers.ListField(required=False, default=[])
    unlisted = serializers.BooleanField(required=False, default=False)

    origin = serializers.CharField(required=False, default="")

    def create(self, validated_data):
        usr = user_deserializer(data=validated_data['author'])


        if usr.is_valid():
            post_usr = usr.create(usr.validated_data)

            tags = validated_data['categories']

        #implement later, working on public stuff rn
            visibleList = []
            for ids in validated_data['visibleTo']:
            # asssuming that either we have the user in here or we dont care, since its guaranteed to be not our user
                u = User.objects.get(id=ids)
                if u:
                    visibleList.append(u)
            categories = []
            for tag in tags:
                if Categories.objects.filter(name=tag).count() == 0:
                    a=Categories.objects.create(name=tag)
                    a.save()
                categories.append(tag)

            try:
                existing_post=Post.objects.get(id=validated_data['id'])
                return None
            except:
                new_post= Post.objects.create(
                    id=validated_data['id'],
                    title=validated_data['title'],
                    source=validated_data['source'],
                    description=validated_data['description'],
                    content_type=contentTypeDict[validated_data['contentType'].lower()],
                    author=post_usr,
                    content=validated_data['content'],
                    published=validated_data['published'],
                    visibility=visilibityDict[validated_data['visibility'].lower()],
                    #visible_to=,
                    unlisted = validated_data['unlisted'],
                    origin = validated_data['origin']
                )
                return new_post

        else:
            print(validated_data['author'])
            print(usr.errors)


# TODO make changes to this
class user_deserializer(serializers.Serializer):
    id = serializers.CharField()
    email = serializers.EmailField(required=False, default='')
    bio = serializers.CharField(required=False, default='')
    host = serializers.CharField(allow_blank=True)
    firstName = serializers.CharField(required=False, default='', allow_blank=True)
    lastName = serializers.CharField(required=False, default='', allow_blank=True)
    displayName = serializers.CharField()
    url = serializers.CharField()
    github = serializers.CharField(allow_null=True, allow_blank=True, default='')

    def create(self, validated_data):
        url_with_id=validated_data['id'].split('/')
        id=url_with_id[-1]
        try:
            usr = User.objects.get(id=id)
            return usr
        except:
            url_with_id = validated_data['id'].split('/')
            id = url_with_id[-1]
            print('created user'+id)
            # also host doesnt have to be our node, can be just random
            # mention this tmr
            try:
                usr = User.objects.create(
                    username = validated_data['displayName'],
                    id=id,
                    #bio=validated_data['bio'],
                    display_name=validated_data['displayName'],
                    local=False
                )

            except:
                a=random.randint(0,1000)
                usr = User.objects.create(
                    username=validated_data['displayName']+str(a),
                    id=id,
                    #bio=validated_data['bio'],
                    display_name=validated_data['displayName'],
                    local=False
                )
            usr.set_unusable_password()
            usr.save()
            return usr