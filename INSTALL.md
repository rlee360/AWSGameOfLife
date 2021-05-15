1. To deploy the system, first adjust the two bucket names in `serverless.yml` to unique names. `bucket` (`GolImgDump`) is the location of the image store, is where the frontend will place the files to process, and where the worker places the files that it has completed working on to be downloaded. `uibucket` (`GolSite`) is the static bucket hosting the webpage.
2. Run `serverless deploy`
3. Update the necessary lines indicated in `static/index.html` to replace the processing bucket name (`bucket`/`GolImgDump`) and the const url with the correct API destination.
4. Run `serverless deploy` again to sync the index file with the bucket.
5. Visit https://[insert uibucket name here].s3.amazonaws.com/index.html
6. Enjoy!