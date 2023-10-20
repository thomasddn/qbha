import paho.mqtt.client as mqtt


class Subscriber:
    def __init__(self) -> None:
        self.topic: str
        self.qos: int = 2


    def can_process(self, msg: mqtt.MQTTMessage) -> bool:
        return self._is_match(msg.topic, self.topic)


    def process(self, client: mqtt.Client, msg: mqtt.MQTTMessage) -> None:
        pass


    def _is_match(self, topic: str, subscription: str) -> bool:
        if topic is None or subscription is None:
            return False
        
        if topic == subscription:
            return True
        
        if subscription == "#":
            return True

        topic = topic.strip().strip("/")
        topic_parts = topic.split("/")
        topic_parts_count = len(topic_parts)

        subscription = subscription.strip().strip("/")
        subscription_parts = subscription.split("/")
        subscription_parts_count = len(subscription_parts)

        if topic_parts_count < subscription_parts_count:
            return False
        
        for i in range(subscription_parts_count):
            subscription_token = subscription_parts[i]

            if subscription_token == "#":
                return True
            
            if subscription_token == "+":
                continue

            if topic_parts[i] == subscription_token:
                continue
            else:
                return False
        
        # It's a match if both have the same length! If subscription ends
        # with a '#' it would have returned True already in the for loop. 
        return topic_parts_count == subscription_parts_count
