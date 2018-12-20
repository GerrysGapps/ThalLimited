# -*- coding: utf-8 -*-
from odoo import http

# class ./projects/customAddons/gaTestModule(http.Controller):
#     @http.route('/./projects/custom_addons/ga_test_module/./projects/custom_addons/ga_test_module/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/./projects/custom_addons/ga_test_module/./projects/custom_addons/ga_test_module/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('./projects/custom_addons/ga_test_module.listing', {
#             'root': '/./projects/custom_addons/ga_test_module/./projects/custom_addons/ga_test_module',
#             'objects': http.request.env['./projects/custom_addons/ga_test_module../projects/custom_addons/ga_test_module'].search([]),
#         })

#     @http.route('/./projects/custom_addons/ga_test_module/./projects/custom_addons/ga_test_module/objects/<model("./projects/custom_addons/ga_test_module../projects/custom_addons/ga_test_module"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('./projects/custom_addons/ga_test_module.object', {
#             'object': obj
#         })