from openerp.tools import mail
try:
	mail.tags_to_kill.remove("iframe")
	mail.tags_to_kill.remove("frame")
except Exception, e:
	print '====',e

allow_element_old = mail._Cleaner.allow_element


def allow_element(self, el):
    if el.tag == 'iframe' or el.tag == 'frame':
        return True
    res = allow_element_old(self, el)
    return res

mail._Cleaner.allow_element = allow_element
