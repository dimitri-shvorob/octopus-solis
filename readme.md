I live in London, buy electricity and gas from Octopus Energy, and have solar panels on my roof.
I ask:
* How much have solar panels saved me to date?
* Is getting a battery worthwhile?
Via its API, Octopus Energy provides smart-meter usage data for 30-minute intervals. My panels
come with SolisCloud app, which does not seem to allow any automatic data collection (please
let me know if that is no longer the case) so I have to collect data manually, and enter it in "data solis.csv".

With these two datasets, I can calculate 
* how much I earned on exported electricity. (Well, Octopus already gives me this info in its app).
* how much I saved on un-imported electricity, i.e. electricity consumed out of own generation.   

Attached code 
* gets usage data from Octopus API (saving daily Parquet files to a subfolder)
* combines Octopus and Solis data
* makes additional calculations
* outputs a Parquet file to feed a simple PowerBI dashboard 