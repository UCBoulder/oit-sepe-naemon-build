RPM Builds for Naemon
=====================

This repo exists because RPMs for Naemon and its various pieces are somewhat scattered across different repositories, and the latest versions are not always compatible with each other. Copying the spec files to one place lets us:

  - Control exactly which version of each piece we use (eg. pull in a particular patch, or switch to a different fork of something)
  - Build all RPMs together so we can be certain all are linked correctly
  - Deliver updates to our nodes as a single "artifact" that can be tested and promoted all together


How to release a new version
----------------------------

1. Create a branch+PR and update spec files as needed. Iterate in there until everything builds successfully.
2. Merge your PR into main.
3. From main, create a [tag](https://git-scm.com/book/en/v2/Git-Basics-Tagging) and push it.
4. Watch the [Actions](https://github.com/UCBoulder/oit-sepe-naemon-build/actions) on this repo to ensure the build succeeds and the release is created.
5. Once the related Action is complete, go to [Releases](https://github.com/UCBoulder/oit-sepe-naemon-build/releases) on this repo and make sure there is a new one that matches your tag.


```
git checkout main
git pull
git tag cub-X.Y.Z
git push origin cub-X.Y.Z
```

NOTE: You can also do this from a branch if you want - probably not the best, but there could be reasons for it. 

And if you run into trouble, you can blow away a tag
```
git tag -d cub-X.Y.Z
git push origin :refs/tags/cub-X.Y.Z
```
Then go delete the release from github, by clicking around and hitting the trash can icon 
