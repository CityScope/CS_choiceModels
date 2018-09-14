# #!/bin/bash
sudo rm -rf dist
# build the /dist for public url 
sudo parcel build index.html 
# make sure to add dist to gitignore [force] 
git add dist -f
#commit the GH pages changes 
git commit -m "table branch commit"
#push to subtree remote [Soft:  git subtree push --prefix dist origin gh-pages]
git push origin `git subtree split --prefix dist master`:table --force
