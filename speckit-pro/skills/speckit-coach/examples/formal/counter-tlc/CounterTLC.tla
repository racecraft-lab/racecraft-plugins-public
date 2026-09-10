---------------------------- MODULE CounterTLC ----------------------------
EXTENDS Integers
CONSTANT Limit
VARIABLE count

Init == count = 0
Next == IF count < Limit THEN count' = count + 1 ELSE UNCHANGED count
Bounded == count >= 0 /\ count <= Limit
Progress == <>(count = Limit)
Spec == Init /\ [][Next]_count /\ WF_count(Next)
=============================================================================
