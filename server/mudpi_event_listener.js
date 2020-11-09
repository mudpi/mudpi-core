var Redis = require('ioredis');
var listener = new Redis({ showFriendlyErrorStack: true });
var plistener = new Redis({ showFriendlyErrorStack: true }); //listener.createClient();
const axios = require('axios')

// Mudpi Event Relay Server v0.2
// This is a nodejs script to catch redis events emitted by the mudpi core and
// relay them to a webhook for further actions such as logging to a database.


// CONFIGS -------------------------
const address = 'test.php'
const channel = '*';
let axiosConfig = {
          headers: {
          'Content-Type': 'application/json;charset=UTF-8',
          "Access-Control-Allow-Origin": "*",
          },
        baseURL: 'http://192.168.2.230/',
        timeout: 1000,
        responseType: 'json'
    };
//------------------------------

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}



plistener.on('connect', function() {
    console.log('\x1b[32mRedis Pattern Listener connected\x1b[0m');
});

plistener.on('error', function (err) {
    console.log('PListener Something went wrong ' + err);
});

listener.on('connect', function() {
    console.log('\x1b[32mRedis Listener connected\x1b[0m');
});

listener.on('error', function (err) {
    console.log('Listener Something went wrong ' + err);
});


let now = new Date().toString().replace(/T/, ':').replace(/\.\w*/, '');
plistener.set('mudpi_relay_started_at', now);
plistener.get('started_at', function (error, result) {
    if (error) {
        console.log(error);
        throw error;
    }

    console.log('Event Relay Started at -> \x1b[32m%s\x1b[0m', now);
    console.log('MudPi System Started at -> \x1b[32m%s\x1b[0m', result);
});


listener.subscribe(channel, (error, count) => {
    if (error) {
        throw new Error(error);
    }
    console.log(`Subscribed to \x1b[36m${count} channel.\x1b[0m Listening for updates on the \x1b[36m${channel} channel.\x1b[0m`);
});

listener.on('message', (channel, message) => {
    console.log(`\x1b[36mMessage Received -\x1b[0m \x1b[37m${channel}\x1b[0m`);
});


plistener.psubscribe(channel, (error, count) => {
    if (error) {
        throw new Error(error);
    }
    console.log(`Client Subscribed to \x1b[36m${count} channel.\x1b[0m Listening for updates on the \x1b[36m${channel} channel.\x1b[0m`);
});

plistener.on('pmessage', (pattern, channel, message) => {
    console.log(`\x1b[36mPattern Message Received on \x1b[1m${channel}\x1b[0m`);
    let eventPromise = relayEvent(message)
    eventPromise.then((response) => {
        try {
            console.log(`\x1b[32mEvent Successfully Relayed. RESPONSE: %s\x1b[0m`,  response.status)

            if(typeof response !== 'undefined' ) {
                  if (response != null && response.hasOwnProperty('data')) {
                    console.log('\x1b[32mResponse Data Received: \x1b[0m', response.data)
                  }
              }
        }
        catch(error) {
            console.log('\x1b[32mEvent Successfully Relayed.\x1b[0m \x1b[31mRESPONSE: Error Decoding Response\x1b[0m')
        }
    })
    .catch((error) => {
        console.log('\x1b[31mRelaying Event FAILED:\x1b[0m')
        console.log(error)
    })
    //console.log(data)
    console.log('\x1b[33mAttempting to Relay Event: \x1b[1m', message, '\x1b[0m')
});


async function relayEvent(event=null) {
      let relayedEvent = null

      try {
        relayedEvent = await axios.post(address, event, axiosConfig)
    }
    catch(e) {
        if(e.code == 'ENETUNREACH') {
            let retries = 3
            while(retries > 1 ) {

                try {
                    console.log('\x1b[31mRelaying the Event Failed [', e.code, ']\x1b[0m')
                    await sleep(5000)
                    console.log('\x1b[33mRetrying Relaying the Event...\x1b[0m')
                    relayedEvent = await axios.post(address, event, axiosConfig)
                }
                catch(e) {
                    console.log('\x1b[31mProblem Resending the Event [', e.code, ']\x1b[0m')
                }

                retries--
            }
        }
        else {
            console.log('\x1b[31mProblem Relaying the Event:\x1b[0m')
            console.error(e)
        }
    }
    
      return relayedEvent
}

