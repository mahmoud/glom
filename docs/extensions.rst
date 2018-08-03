``glom`` Extension System
=========================

While glom comes with a lot of built-in features, no library can ever
be truly complete when it comes to data manipulation.

To cover every case out there, glom provides a method of adding your
own data handling hooks alongside the standard functionality. This
document explains glom's execution model and how to integrate with it
using glom's Extension API.

Making a Specifier Type
-----------------------

The glom Scope
--------------
