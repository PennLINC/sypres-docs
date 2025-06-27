# sypres.io
:triangular_ruler: Website for [sypres](https:syprs.io) Project

### building and serving locally

If you haven't installed ruby:

```
brew install rbenv ruby-build
rbenv install 3.1.4 # current version of ruby the website uses
eval "$(rbenv init -)"
```

You only need to run this command once:
```
bundle install
```

Then you can serve locally anytime using:
```
bundle exec jekyll serve
```

If your terminal session is restarted, you may need to re-run the eval command when you come back.
Then you can run `bundle exec jekyll serve` again and it should work.
If you're having trouble, check that the version is correct: `ruby -v`.