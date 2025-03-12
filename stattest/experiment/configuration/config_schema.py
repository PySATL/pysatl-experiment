CONF_SCHEMA = {
    "type": "object",
    "properties": {
        "max_open_trades": {
            "description": "Maximum number of open trades. -1 for unlimited.",
            "type": ["integer", "number"],
            "minimum": -1,
        },
        "timeframe": {
            "description": "The timeframe to use (e.g `1m`, `5m`, `15m`, `30m`, `1h` ...).",
            "type": "string",
        },
        "stake_currency": {
            "description": "Currency used for staking.",
            "type": "string",
        },
        "stake_amount": {
            "description": "Amount to stake per trade.",
            "type": ["number", "string"],
            "minimum": 0.0001,
            "pattern": "",
        },
    },
}
