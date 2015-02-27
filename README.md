* Introduction *

This library provides datastructures and algorithms for formal argumentation. 
The library supports both abstract and instantiated argumentation.
The abstract argumentation part uses unrestricted rebut where arguments
can attack each other as long as at least one of the rules used in an argument
is a defeasible rule.


* Installation *

The library uses pyparsing to parse the knolwedge base rules.
To use the library, clone it into your project and use it.


* Knowledge Base Format *

A consequent is true if all of its antecedents are true.

Negation:
-literal 

Strict rules:
--> consequent
antecedent --> consequent
antecedent1, antecedent2, ..., antecedentN --> consequent

Defeasible rules:
==> consequent
antecedent ==> consequent
antecedent1, antecedent2, ..., antecedentN ==> consequent

Defeaible rules with undercutters:
=(vulnerability)=> consequent
=(vulnerability1,vulnerability2)=> consequent

Rules can have an optional name
Name: p --> q

User can also specify preference of defeasible rules:
R1 < R2

This means that when two arguments attack each other, the argument based on R2
is stronger than the argument based on R1.


Below is an example of a knowledge base file:
################################################################################
--> jw
--> mw
--> sw
mt, st --> -jt
jt, mt --> -st
jt, st --> -mt

R1: jw ==> jt
R2: mw ==> mt
sw ==> st

# preference:

R2 < R1 

=(-foo)=> bar # unless foo, assume bar - if 'foo' is not asserted, assert 'bar'
################################################################################
