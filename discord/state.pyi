# NOTE: ConnectionState should never be accessed by the user and is only included
# here in order to be used in Webhook.from_state(). For these reasons, it is declared
# as an opaque structure

class ConnectionState:
    ...

class AutoShardedConnectionState(ConnectionState):
    ...
