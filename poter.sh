#!/bin/bash
#
# Script to create pot/po/mo files 

basedir="/home/smo/Documents/gmediafinder/po"
cd "/home/smo/Documents/gmediafinder"

if [ "$1" = "cmo" ]; then
echo "genere le .mo"
## finalise en creeant le .mo
mkdir -p $basedir/fr/LC_MESSAGES
mkdir -p $basedir/en/LC_MESSAGES
mkdir -p $basedir/it/LC_MESSAGES
mkdir -p $basedir/ro/LC_MESSAGES
msgfmt --output-file=$basedir/fr/LC_MESSAGES/gmediafinder.mo $basedir/fr.po
msgfmt --output-file=$basedir/en/LC_MESSAGES/gmediafinder.mo $basedir/en.po
msgfmt --output-file=$basedir/it/LC_MESSAGES/gmediafinder.mo $basedir/it.po
msgfmt --output-file=$basedir/ro/LC_MESSAGES/gmediafinder.mo $basedir/ro.po
exit 0
fi

## cree pot fichier glade et des .py
xgettext -k_ -kN_ -o $basedir/gmediafinder.pot $(find /home/smo/Documents/gmediafinder | egrep "\.glade|[a-zA-Z].py$|\.pot" | xargs)

## create or update po files
LANGLIST="en fr it ro"
for lang in $LANGLIST; do
if [ ! -e "$basedir"/$lang.po ]; then
	msginit --input=$basedir/gmediafinder.pot --output=$basedir/$lang.po --locale=$lang_$(echo "$lang" | tr '[:lower:]' '[:upper:]')
else
	msginit --input=$basedir/gmediafinder.pot --output=$basedir/$lang-update.po --locale=$lang_$(echo "$lang" | tr '[:lower:]' '[:upper:]')
	msgmerge -U $basedir/$lang.po $basedir/$lang-update.po
	## clean files
	rm $basedir/$lang-update.po
	rm $basedir/$lang.po~
fi
done
