from random import choice

from pyretic.lib.corelib import *
from pyretic.lib.std import *
from pyretic.lib.query import *

from pyretic.pyresonance.fsm_policy import *
from pyretic.pyresonance.drivers.json_event import JSONEvent 
from pyretic.pyresonance.smv.translate import *
from pyretic.pyresonance.apps.mac_learner import *
from pyretic.pyresonance.apps.monitor import *

    

#####################################################################################################
# * App launch
#   - pyretic.py pyretic.pyresonance.apps.rate_limiter
#
# * Mininet Generation (in "~/pyretic/pyretic/pyresonance" directory)
#   - sudo mn --controller=remote,ip=127.0.0.1 --mac --arp --switch ovsk --link=tc --custom mininet_topos/example_topos.py --topo=ratelimit
#
# * Start ping from h1 to h2 
#   - mininet> h1 ping h2
#
# * Events to rate limit to level '2' (100ms delay bidirectional) (in "~/pyretic/pyretic/pyresonance" directory)
#   - python json_sender.py -n rate -l 2 --flow="{srcip=10.0.0.1,dstip=10.0.0.2}" -a 127.0.0.1 -p 50001
#
# * Events to rate limit to level '3' (400ms delay bidirectional) (in "~/pyretic/pyretic/pyresonance" directory)
#   - python json_sender.py -n rate -l 3 --flow="{srcip=10.0.0.1,dstip=10.0.0.2}" -a 127.0.0.1 -p 50001
#
# * Events to rate limit back to level '1' (no delay) (in "~/pyretic/pyretic/pyresonance" directory)
#   - python json_sender.py -n rate -l 1 --flow="{srcip=10.0.0.1,dstip=10.0.0.2}" -a 127.0.0.1 -p 50001
#
#####################################################################################################



class rate_limiter(DynamicPolicy):
    def __init__(self):

        ### DEFINE INTERNAL METHODS
        
        rates = [1,2,3]

        def interswitch():
            return if_(match(inport=2),fwd(1),fwd(2))

        def routing():
            match_inter = union([match(switch=2),match(switch=3),match(switch=4)])
            match_inport = union([match(inport=2),match(inport=3),match(inport=4)])

            r = if_(match_inter,interswitch(), if_(match_inport, fwd(1), drop))
            
            return r

        def rate_limit_policy(i):
            match_from_edge = (union([match(switch=1),match(switch=5)]) & match(inport=1))
            return if_(match_from_edge, fwd(i), routing())


        ### DEFINE THE LPEC FUNCTION
        def lpec(f):
            h1 = f['srcip']
            h2 = f['dstip']
            return union([match(srcip=h1,dstip=h2),match(srcip=h2,dstip=h1)] )


        ### SET UP TRANSITION FUNCTIONS

        @transition
        def rate(self):
            self.case(occured(self.event),self.event)

        @transition
        def policy(self):
            for i in rates:
                self.case(V('rate')==C(i), C(rate_limit_policy(i+1)))

        ### SET UP THE FSM DESCRIPTION
    
        self.fsm_def = FSMDef( 
            rate=FSMVar(type=Type(int,set(rates)),
                         init=1,
                         trans=rate),
            policy=FSMVar(type=Type(Policy,set([rate_limit_policy(i+1) for i in rates ])),
                           init=rate_limit_policy(2),
                           trans=policy))

        # Instantiate FSMPolicy, start/register JSON handler.
        fsm_pol = FSMPolicy(lpec, self.fsm_def)
        json_event = JSONEvent()
        json_event.register_callback(fsm_pol.event_handler)
        
        super(rate_limiter,self).__init__(fsm_pol)


def main():
    pol = rate_limiter()

    # For NuSMV
    smv_str = fsm_def_to_smv_model(pol.fsm_def)
    mc = ModelChecker(smv_str,'rate_limiter')  

    ## Add specs 
    mc.add_spec("SPEC AG (rate=1 -> AX policy=policy_91447278467441041390399171817158164370)")
    mc.add_spec("SPEC AG (rate=2 -> AX policy=policy_307570358292051343788859313047439814038)")
    mc.add_spec("SPEC AG (rate=3 -> AX policy=policy_337212563897699033245338971435270463530)")
    mc.add_spec("SPEC AG (EF policy=policy_91447278467441041390399171817158164370)")
    mc.add_spec("SPEC AG (policy=policy_91447278467441041390399171817158164370 -> EF policy=policy_307570358292051343788859313047439814038)")
 
    mc.save_as_smv_file()
    mc.verify()

#    return pol
    return pol >> monitor()

