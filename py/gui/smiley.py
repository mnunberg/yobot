#!/usr/bin/env python
#simple smileys icon builder..
SMILEYS_INDEX=(
"""
# Default smileys
[default]
happy.png           :)      :-)
excited.png         :-D     :-d     :D      :d
sad.png             :-(     :(
wink.png            ;-)     ;)
tongue.png          :P      :p      :-P     :-p
shocked.png         =-O     =-o
kiss.png            :-*
glasses-cool.png    8-)
embarrassed.png     :-[
crying.png          :'(     :'-(
thinking.png        :-/     :-\\
angel.png           O:-)    o:-)
shut-mouth.png      :-X
moneymouth.png      :-$
foot-in-mouth.png   :-!
shout.png           >:o     >:O
 skywalker.png     C:-)    c:-)    C:)     c:)
 monkey.png        :-(|)   :(|)    8-|)
 cyclops.png       O-)     o-)


[XMPP]
# Following XEP-0038 + GTalk + our default set, in default set order
# The GTalk strings come from ticket #3307.
happy.png           :)      :-)     =)
excited.png         :-D     :-d     :D      :d      =D      =d
sad.png             :-(     :(
wink.png            ;-)     ;)      ;^)
tongue.png          :P      :p      :-P     :-p
shocked.png         =-O     =-o     :-O     :-o
kiss.png            :kiss:  :-*
glasses-cool.png    8-)     B-)
embarrassed.png     :-[
crying.png          :'-(    :'(
thinking.png        :-/     :-\\
angel.png           O:-)    o:-)
shut-mouth.png      :-X
moneymouth.png      :-$
foot-in-mouth.png   :-!
shout.png           >:o     >:O

# Following XEP-0038 + GTalk
angry.png           >:-(    >:(     X-(    x-(
good.png            :yes:
bad.png             :no:
stop.png            :wait:
rose.png            @->--   :rose:
phone.png           :telephone:
mail.png            :email:
lamp.png            :jabber:
cake.png            :cake:
in_love.png         :heart: :love:  <3
love-over.png       :brokenheart:
musical-note.png    :music:
beer.png            :beer:
coffee.png          :coffee:
coins.png           :money:
moon.png            :moon:
sun.png             :sun:
star.png            :star:

# Others
neutral.png         :|      :-|
victory.png         \\m/

# Hidden icons from the default set.
 skywalker.png     C:-)    c:-)    C:)     c:)
 monkey.png        :-(|)   :(|)    8-|)
 cyclops.png       O-)     o-)


# Following AIM 6.1
[AIM]
happy.png           :-)     :)
wink.png            ;-)     ;)
sad.png             :-(     :(
tongue.png          :P      :p      :-P     :-p
shocked.png         =-O
kiss.png            :-*
shout.png           >:o
excited.png         :-D     :D
moneymouth.png      :-$
foot-in-mouth.png   :-!
embarrassed.png     :-[
angel.png           O:-)
thinking.png        :-\\    :-/
crying.png          :'(
shut-mouth.png      :-X
glasses-cool.png    8-)
 skywalker.png     C:-)    c:-)    C:)     c:)
 monkey.png        :-(|)   :(|)    8-|)
 cyclops.png       O-)     o-)


# Following Windows Live Messenger 8.1
[MSN]
happy.png           :)      :-)
excited.png         :D      :d      :-D     :-d
wink.png            ;)      ;-)
shocked.png         :-O     :-o     :O      :o
tongue.png          :-P     :P      :-p     :p
glasses-cool.png    (H)     (h)
angry.png           :@      :-@
embarrassed.png     :$      :-$
confused.png        :S      :s      :-S     :-s
sad.png             :(      :-(
crying.png          :'(
neutral.png         :|      :-|
devil.png           (6)
angel.png           (A)     (a)
in_love.png         (L)     (l)
love-over.png       (U)     (u)
msn.png             (M)     (m)
cat.png             (@)
dog.png             (&)
moon.png            (S)
star.png            (*)
film.png            (~)
musical-note.png    (8)
mail.png            (E)     (e)
rose.png            (F)     (f)
rose-dead.png       (W)     (w)
clock.png           (O)     (o)
kiss.png            (K)     (k)
present.png         (G)     (g)
cake.png            (^)
camera.png          (P)     (p)
lamp.png            (I)     (i)
coffee.png          (C)     (c)
phone.png           (T)     (t)
hug-left.png        ({)
hug-right.png       (})
beer.png            (B)     (b)
drink.png           (D)     (d)
boy.png             (Z)     (z)
girl.png            (X)     (x)
good.png            (Y)     (y)
bad.png             (N)     (n)
vampire.png         :[      :-[
goat.png            (nah)
sun.png             (#)
rainbow.png         (R)     (r)
quiet.png           :-#
teeth.png           8o|
glasses-nerdy.png   8-|
sarcastic.png       ^o)
secret.png          :-*
sick.png            +o(
snail.png           (sn)
turtle.png          (tu)
plate.png           (pl)
bowl.png            (||)
pizza.png           (pi)
soccerball.png      (so)
car.png             (au)
airplane.png        (ap)
umbrella.png        (um)
island.png          (ip)
computer.png        (co)
mobile.png          (mp)
brb.png             (brb)
rain.png            (st)
highfive.png        (h5)
coins.png           (mo)
sheep.png           (bah)
dont-know.png       :^)
thinking.png        *-)
thunder.png         (li)
party.png           <:o)
eyeroll.png         8-)
sleepy.png          |-) 
bunny.png           ('.')
 skywalker.png     C:-)    c:-)    C:)     c:)
 monkey.png        :-(|)   :(|)    8-|)
 cyclops.png       O-)     o-)

# Hidden MSN emotes
cigarette.png      	(ci)    (CI)
handcuffs.png       (%)
console.png			(xx)    (XX)
fingers-crossed.png	(yn)    (YN)


# Following QQ 2006
[QQ]
shocked.png         /:O      /jy       /surprised
curl-lip.png        /:~      /pz       /curl_lip
desire.png          /:*      /se       /desire
dazed.png           /:|      /dazed
party.png           /8-)     /dy       /revel
crying.png          /:<      /ll       /cry
bashful.png         /:$      /hx       /bashful
shut-mouth.png      /:X      /bz       /shut_mouth
sleeping.png        /:Z      /shui     /sleep
weep.png            /:'(     /dk       /weep
embarrassed.png     /:-|     /gg       /embarassed
pissed-off.png      /:@      /fn       /pissed_off
act-up.png          /:P      /tp       /act_up
excited.png         /:D      /cy       /toothy_smile
happy.png           /:)      /wx       /small_smile
sad.png             /:(      /ng       /sad
glasses-cool.png    /:+      /kuk      /cool
doctor.png          /:#      /feid     /SARS
silly.png           /:Q      /zk       /crazy
sick.png            /:T      /tu       /vomit
snicker.png         /;p      /tx       /titter
cute.png            /;-D     /ka       /cute
disdain.png         /;d      /by       /disdain
arrogant.png        /;o      /am       /arrogant
starving.png        /:g      /jie      /starving
sleepy.png          /|-)     /kun      /sleepy
terror.png          /:!      /jk       /terror
hot.png             /:L      /sweat
smirk.png           /:>      /hanx     /smirk
soldier.png         /:;      /db       /soldier
struggle.png        /;f      /fendou   /struggle
curse.png           /:-S     /zhm      /curse
question.png        /?       /yiw      /question
quiet.png           /;x      /xu       /shh
hypnotized.png      /;@      /yun      /dizzy
excruciating.png    /:8      /zhem     /excrutiating
freaked-out.png     /;!      /shuai    /freaked_out
skeleton.png        /!!!     /kl       /skeleton
hammer.png          /xx      /qiao     /hammer
bye.png             /bye     /zj       /bye
go-away.png         /go      /shan     /go
afraid.png          /shake   /fad      /shake
amorous.png         /love    /aiq      /love
jump.png            /jump    /tiao     /jump
search.png          /find    /zhao     /search
lashes.png          /&       /mm       /beautiful_eyebrows
pig.png             /pig     /zt       /pig
cat.png             /cat     /mm       /cat
dog.png             /dog     /xg       /dog
hug-left.png        /hug     /yb       /hug
coins.png           /$       /qianc    /money
lamp.png            /!       /dp       /lightbulb
bowl.png            /cup     /bei      /cup
cake.png            /cake    /dg       /cake
thunder.png         /li      /shd      /lightning
bomb.png            /bome    /zhd      /bomb
knife.png           /kn      /dao      /knife
soccerball.png      /footb   /zq       /soccer
musical-note.png    /music   /yy       /music
poop.png            /shit    /bb       /shit
coffee.png          /coffee  /kf       /coffee
hungry.png          /eat     /fan      /eat
pill.png            /pill    /yw       /pill
rose.png            /rose    /mg       /rose
wilt.png            /fade    /dx       /wilt
kiss.png            /kiss    /wen      /kiss
in_love.png         /heart   /xin      /heart
love-over.png       /break   /xs       /broken_heart
meeting.png         /meeting /hy       /meeting
present.png         /gift    /lw       /gift
phone.png           /phone   /dh       /phone
clock.png           /time    /sj       /time
mail.png            /email   /yj       /email
tv.png              /TV      /ds       /TV
sun.png             /sun     /ty       /sun
moon.png            /moon    /yl       /moon
good.png            /strong  /qiang    /thumbs_up
bad.png             /weak    /ruo      /thumbs_down
handshake.png       /share   /ws       /handshake
victory.png         /v       /shl      /victory
beauty.png          /<J>     /mn       /beauty
qq.png              /<QQ>    /qz       /qq
blowkiss.png        /<L>     /fw       /blow_kiss
angry.png           /<O>     /oh       /angry
liquor.png          /<B>     /bj       /baijiu
can.png             /<U>     /qsh      /soda
watermelon.png      /<W>     /xigua    /watermelon
rain.png            /<!!>    /xy       /rain
cloudy.png          /<~>     /duoy     /cloudy
snowman.png         /<Z>     /xr       /snowman
star.png            /<*>     /xixing   /star
girl.png            /<00>    /nv       /woman
boy.png             /<11>    /nan      /man
 skywalker.png     C:-)    c:-)    C:)     c:)
 monkey.png        :-(|)   :(|)    8-|)
 cyclops.png       O-)     o-)


# Following ICQ 6.0
[ICQ]
happy.png           :-)     :)
neutral.png         :-$
sad.png             :-(     :(
shocked.png         =-O
wink.png            ;-)     ;)
tongue.png          :-P     :P      :-p     :p
music.png           [:-}
laugh.png           *JOKINGLY*
sleeping.png        *TIRED*
crying.png          :'(    :'-(
sick.png            :-!
kissed.png          *KISSED*
stop.png            *STOP*
kiss.png            :-{} :-*
kissing.png         *KISSING* 
victory.png         *YAHOO*
silly.png           %)
embarrassed.png     :-[
devil.png           ]:->
angel.png           O:-)
rose.png            @}->--
shut-mouth.png      :-X     :X      :-x     :x
bomb.png            @=
thinking.png        :-\\    :-/
good.png            *THUMBS\ UP*
shout.png           >:o     >:O     :-@
beer.png            *DRINK*
excited.png         :-D     :D
glasses-cool.png    8-)
amorous.png         *IN\ LOVE*
 skywalker.png     C:-)    c:-)    C:)     c:)
 monkey.png        :-(|)   :(|)    8-|)
 cyclops.png       O-)     o-)


# Following Yahoo! Messenger 8.1
[Yahoo]
happy.png           :)      :-)
question.png        :-/     :-\\
shocked.png         :-O     :O      :-o     :o 
devil.png           >:)
angel.png           O:-)    o:-)    0:-)
sick.png            :-&
sleepy.png          (:|
hypnotized.png      @-)
on-the-phone.png    :)]
sad.png             :(      :-(
amorous.png         :x      :-x     :X      :-X
angry.png           X-(     x-(     X(      x(
crying.png          :((
glasses-nerdy.png   :-B     :-b
quiet.png           :-$
drool.png           =P~     =p~
lying.png           :^O     :^o
call-me.png         :-c
wink.png            ;)      ;-)
embarrassed.png     :">
mean.png            :->     :>
laugh.png           :))     :-))
bye.png             =;
arrogant.png        [-(
thinking.png        :-?
waiting.png         :-w     :-W
at-wits-end.png     ~x(     ~X(
excited.png         :D      :-D     :d      :-d
tongue.png          :-P     :P      :-p     :p
glasses-cool.png    B-)     b-)
neutral.png         :|      :-|
sleeping.png        I-)     i-)     |-)
clown.png           :o)     :O)
doh.png             #-o     #-O
weep.png            :-<
go-away.png         :-h
lashes.png          ;;)
kiss.png            :-*     :*
confused.png        :-S     :-s
sarcastic.png       /:)
eyeroll.png         8-|
silly.png           8-}
clap.png            =D>     =d>
mad-tongue.png      >:P     >:p
time-out.png        :-t     :-T
hug-left.png        >:D<    >:d<
love-over.png       =((
hot.png             #:-S    #:-s
rotfl.png           =)) :-j :-J 
loser.png           L-)     l-)
party.png           <:-P    <:-p
nervous.png         :-SS	:-Ss	:-sS	:-ss
cowboy.png          <):)
desire.png          8->
 skywalker.png     C:-)    c:-)    C:)     c:)
 monkey.png        :-(|)   :(|)    8-|)
 cyclops.png       O-)     o-)

# Hidden Yahoo emotes
alien.png           =:)     >-)
beat-up.png         b-(     B-(
chicken.png         ~:>
coffee.png          ~o)     ~O)
cow.png             3:-O    3:-o
dance.png           \\:D/   \\:d/
rose.png            @};-
dont-know.png       :-L     :-l
skeleton.png        8-X     8-x
lamp.png            *-:)
monkey.png          :(|)
coins.png           $-)
peace.png           :)>-
pig.png             :@)
pray.png            [-o<    [-O<
pumpkin.png         (~~)
shame.png           [-X     [-x
flag.png            **==
clover.png          %%-
musical-note.png    :-"
giggle.png          ;))
worship.png         ^:)^
star.png            (*)
waving.png          >:/
talktohand.png      :-@

# Only available after activating the Yahoo! Fighter IMVironment
male-fighter1.png   o->     O->
male-fighter2.png   o=>     O=>
female-fighter.png  o-+     O-+
yin-yang.png        (%)


# Following MySpaceIM Beta 1.0.697.0
[MySpaceIM]
excited.png  	    :D      :-D
devil.png	    }:)
confused.png	    :Z
glasses-nerdy.png   B)
bulgy-eyes.png	    %)
freaked-out.png	    :E
smile.png	    :)      :-)
amorous.png	    :X
laugh.png	    :))
mohawk.png	    -:
mad-tongue.png	    X(
messed.png	    X)
glasses-nerdy.png   Q)
doh.png		    :G
pirate.png	    P)
shocked.png	    :O
sidefrown.png	    :{
sinister.png	    :B
smirk.png	    :,
neutral.png	    :|
tongue.png	    :P      :p
pissed-off.png	    B|
wink.png	    ;-)     ;)
sad.png		    :[
kiss.png            :x
 skywalker.png     C:-)    c:-)    C:)     c:)
 monkey.png        :-(|)   :(|)    8-|)
 cyclops.png       O-)     o-)


# MXit standard emoticons
[MXit]
happy.png           :-)     :)
sad.png             :-(     :(
wink.png            ;-)     ;)
excited.png         :-D     :D     :->      :>
neutral.png         :-|     :|
shocked.png         :-O     :O
tongue.png          :-P     :P
embarrassed.png     :-$     :$
glasses-cool.png    8-)
in_love.png         (H)
rose.png            (F)
### Added in v3.0
boy.png             (m)
girl.png            (f)
star.png            (*)
chilli.png          (c)
kiss.png            (x)
lamp.png            (i)
pissed-off.png      :e      :-e
shut-mouth.png      :-x     :x
thunder.png         (z)
coffee.png          (U)
mrgreen.png         (G)
### Added in v5.0
sick.png            :o(
excruciating.png    :-{     :{
amorous.png         :-}     :}
eyeroll.png         8-o     8o
crying.png          :'(
thinking.png        :-?     :?
drool.png           :-~     :~
sleeping.png        :-z     :z
lying.png           :L)
glasses-nerdy.png   8-|     8|
pirate.png          P-)
### Added in v5.9.7
bored.png           :-[     :[
cold.png            :-<     :<
confused.png        :-,     :,
hungry.png          :-C     :C
stressed.png        :-s     :s
""")

import sys
sys.path.append("../")
import yobotproto
import yobotops
from re import escape as re_escape
import re
from cgi import escape as html_escape
tbl = {}


#ok, some major cleanup here...
#some simple groupings...

class SmileyRegistry(object):
    def __init__(self):
        #indexed by improto
        self.regexp = {}
        #indexed by (smiley_code, improto)
        self.resourcetable = {}
        self.allsmileys = {}
    def addsmiley(self, improto, smiley):
        self.allsmileys.setdefault(improto, set()).add(smiley)
    def getsmileys(self, improto):
        return self.allsmileys[improto]

DEFAULT_SCHEME = -256
UNUSED = -16

htmlescaped = SmileyRegistry()
plain = SmileyRegistry()

def gensmileys():
    current_protocol = None
    for l in SMILEYS_INDEX.split("\n"):
        l = l.strip()
        if not l:
            continue
        if l.startswith("#"):
            continue
        if l.startswith("["):
            proto_name = l.strip("[]").lower()
            if proto_name == "xmpp":
                current_protocol = yobotproto.YOBOT_JABBER
            elif proto_name == "aim":
                current_protocol = yobotproto.YOBOT_AIM
            elif proto_name == "msn":
                current_protocol = yobotproto.YOBOT_MSN
            elif proto_name == "yahoo":
                current_protocol = yobotproto.YOBOT_YAHOO
            elif proto_name == "default":
                current_protocol = DEFAULT_SCHEME
            else:
                current_protocol = UNUSED
            continue
        
        if not current_protocol:
            continue
        items = l.split()
        name, emotes = items[0], items[1:]
        for emote in emotes:
            htmled = html_escape(emote)
            
            htmlescaped.resourcetable[(htmled, current_protocol)] = name
            htmlescaped.addsmiley(current_protocol, htmled)
            
            plain.resourcetable[(emote, current_protocol)] = name
            plain.addsmiley(current_protocol, emote)
            
    for o in (plain, htmlescaped):
        for k, v in o.allsmileys.items():
            o.regexp[k] = re.compile("(%s)" % ("|".join([re.escape(s) for s in sorted(v,key=len, reverse=True)])))

try:
    import cPickle as pickle
    plain, htmlescaped = pickle.load(open("/tmp/.yobot_smileys_cached.pickle", "r"))
    print "imported from pickle"
except Exception, e:
    print e
    gensmileys()
    try:
        pickle.dump((plain, htmlescaped), open("/tmp/.yobot_smileys_cached.pickle", "w"))
    except Exception, e:
        print e
#gensmileys()

if __name__ == "__main__":
    sys.exit()
    for k, v in plain.resourcetable.items():
        smiley, proto = k
        print "%-15s %-15s -> %s" % (smiley, yobotops.imprototostr(proto), v)
    for k, v in plain.allsmileys.items():
        print yobotops.imprototostr(k)
        items = "\t"
        counter = 0
        for i in v:
            i += " "
            items += i
            counter += len(i)
            if counter >= 70:
                items += "\n\t"
                counter = 0
        print items