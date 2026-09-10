----------------------------- MODULE Counter -----------------------------
EXTENDS Integers
CONSTANT
    \* @type: Int;
    Limit
VARIABLE
    \* @type: Int;
    count

Init == count = 0
Next == IF count < Limit THEN count' = count + 1 ELSE UNCHANGED count
Bounded == count >= 0 /\ count <= Limit
Spec == Init /\ [][Next]_count
=============================================================================
