

from ..policies.base_policy import *
from ..FSMs.base_fsm import *

from ..globals import *

class AuthFSM_T(BaseFSM_T):
    
    def default_handler(self, message, queue):
        return_value = 'ok'
        
        if DEBUG == True:
            print "Auth handler: ", message['flow']
            
        if message['event_type'] == EVENT_TYPES['auth']:
            if message['message_type'] == MESSAGE_TYPES['state']:
                self.state_transition(message['message_value'], message['flow'], queue)
            elif message['message_type'] == MESSAGE_TYPES['info']:
                pass
            elif message['message_type'] == MESSAGE_TYPES['query']:
                state_str = self.get_state(message['flow'])
                return_str = "\n*** State information in module (" + self.module_name + ") ***"
                return_str = return_str + "\n* Flow: " + str(message['flow'])
                return_str = return_str + "\n* State: " + str(state_str) + '\n'
                print return_str
                return_value = return_str
        else:
            print "Auth: ignoring message type."
            
        return return_value