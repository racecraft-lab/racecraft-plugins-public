---- MODULE Counter ----
EXTENDS Integers
CONSTANT
  \* @type: Int;
  Start
CONSTANT
  \* @type: Int;
  Limit
VARIABLE
  \* @type: Int;
  count
Init == count = Start
Increment == count < Limit /\ count' = count + 1
Hold == count = Limit /\ count' = count
Next == Increment \/ Hold
Bounded == count >= Start /\ count <= Limit
====
