
the goal is:

When the class is instantiated it should

make logger
setup default vars

establish websocket connection
subscribe to data
get snapshot data

continue getting new update data
    append when new data 

methods for accessing the data
periodic method for making sure data isnt growing too large





1. add establish websocket def
    1. subscribe to data
    2. get snapshot data
    3. get update data
        1. append when new data 

3. get data(duration = seconds)
    2. trim data to selection
    return df

the current script is:


