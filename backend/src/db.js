const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const genericPool = require('generic-pool');

const dbPath = path.resolve(__dirname, 'database.sqlite');

// Initialize schema once
const initDb = new sqlite3.Database(dbPath, (err) => {
    if (err) {
        console.error('Error opening database for initialization', err);
    } else {
        initDb.run(`CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password TEXT
        )`, (err) => {
            if (err) {
                console.error('Error initializing schema', err);
            }
            initDb.close();
        });
    }
});

const factory = {
    create: function() {
        return new Promise((resolve, reject) => {
            const client = new sqlite3.Database(dbPath, (err) => {
                if (err) {
                    console.error('Error opening database connection', err);
                    reject(err);
                } else {
                    resolve(client);
                }
            });
        });
    },
    destroy: function(client) {
        return new Promise((resolve, reject) => {
            client.close((err) => {
                if (err) reject(err);
                else resolve();
            });
        });
    }
};

const pool = genericPool.createPool(factory, {
    max: 10,
    min: 2
});

function wrapMethod(methodName) {
    return async function(sql, ...args) {
        let callback = null;
        if (args.length > 0 && typeof args[args.length - 1] === 'function') {
            callback = args.pop();
        }

        let client;
        try {
            client = await pool.acquire();
            // We need to inject our own callback to release the client and then call the original callback
            const wrappedCallback = function(...cbArgs) {
                pool.release(client);
                if (callback) {
                    callback.apply(this, cbArgs);
                }
            };

            client[methodName](sql, ...args, wrappedCallback);
        } catch (err) {
            if (client) {
                try {
                    pool.release(client);
                } catch (releaseErr) {
                    console.error('Failed to release client', releaseErr);
                }
            }
            if (callback) {
                callback.call(this, err);
            }
        }
    };
}

const dbWrapper = {
    run: wrapMethod('run'),
    get: wrapMethod('get'),
    all: wrapMethod('all')
};

module.exports = dbWrapper;