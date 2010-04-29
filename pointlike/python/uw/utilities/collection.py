"""
generate collection file for LiveLabs Pivot viewer

$Header$
See <http://getpivot.com>
Author: Toby Burnett <tburnett@uw.edu>
"""

import os, pickle, pyfits, types
import xml.sax

import numpy as np

def get_image_ids( dzc):
    """ look for the names in the DZC file 
    
    """
    class Handler(xml.sax.ContentHandler):
        def __init__(self):
            self.id_dict={}
        def startElement(self, name, attrs):
            if name == "I":
                id = attrs['Id']
                source =attrs['Source']
                fname =os.path.split(source)[1]
                self.id_dict[fname]=id
    parser = xml.sax.make_parser()
    h=Handler()
    parser.setContentHandler(h)
    parser.parse(open(dzc,'r'))
    return h.id_dict

class Collection(object):
    """ manage a collection object.
    
    """
    header="""<?xml version="1.0"?>\n<Collection 
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
    xmlns:xsd="http://www.w3.org/2001/XMLSchema" 
    Name="%s" 
    SchemaVersion="1" 
    xmlns:d1p1="http://schemas.microsoft.com/livelabs/pivot/collection/2009" 
    xmlns="http://schemas.microsoft.com/collection/metadata/2009" %s>"""

    trailer = """\n</Collection> """ 


    def __init__(self, cname, folder, item_names, dzc, img_list=None, icon=None, href=None):
        """
        parameters description
        ---------- -----------
        cname       name for the collection
        folder     folder where files exist, the result will be put
        item_names list of names for each item
        dzc        filename for the Deep Zoom (DZ) Collection of images, relative to base
        img_list  if specified, a list of integers for the images in the DZ collection corresponding to the names
        href      list of references
       
        """
        self.name = cname
        self.folder = folder
        assert(os.path.exists(folder))
        self.facets =[]
        self.item_names = item_names
        self.n = len(item_names)
        assert(self.n>0)
        self.dzc = dzc
        full_dzc = os.path.join(folder,dzc)
        assert( os.path.exists(full_dzc))
        if img_list is not None:
            self.img_list = img_list
            assert(len(img_list)==self.n)
        else:
            ids = get_image_ids(full_dzc)
            # 
            names = [n.replace('+', 'p').replace(' ','_')  for n in item_names]
            try:
                self.img_list = [ids[n+'.xml'] for n in names]
            except:
                print 'Source not found in list of images %s' % img_list
                raise
        self.icon = icon
        self.href=href

    class Facet(object):
        def __init__(self, name, type, format, data, filter):
            self.name,self.type,self.format, self.data, self.filter= name,type,format,data,filter
                
    def add_facet(self, name, type, format, data, filter='true'):
        """add a Facet to the collection.
        
        parameters description
        ---------- -----------
        name       facet name
        type       type, one of String, LongString, Number, DateTime, or Link
        format     format to use for info ('C', 'F', 'D')
        data       array of values. For String, each value can be an array itself
        
        """
        assert( type in 'String Number LongString DateTime Link'.split())
        assert(len(data)==self.n) # make sure all columns the same length
        self.facets.append(Collection.Facet(name, type, format, data, filter))
        
    def write(self, outfile):
        assert(len(self.facets)>0) # fail if no Facets were added
        out= open(outfile, 'w')
        out.write(Collection.header %  (self.name, ('' if self.icon is None else ' d1p1:Icon="%s"'%self.icon) ))

        out.write('\n<FacetCategories>' )
        for facet in self.facets:
            #IsFilterVisible="%(filter)s"
            out.write('\n  <FacetCategory Name="%(name)s" Type="%(type)s" Format="%(format)s" d1p1:IsFilterVisible="%(filter)s"/>' %(facet.__dict__))
        out.write('\n</FacetCategories>')
        
        out.write('\n<Items ImgBase="%s">' %  self.dzc)
        for i,name in enumerate(self.item_names):
            img = self.img_list[i]
            href= ' Href="%s"' % self.href[i] if self.href is not None else ""
            out.write('\n<Item Id="%d" Img="#%d" Name="%s" %s>' % (i, int(img), name, href))
            out.write('\n <Facets>')
            for facet in self.facets:
                if facet.type == 'Number':
                    datum = facet.data[i]
                    out.write('\n  <Facet Name="%s"> <%s Value="%.4f"/> </Facet>' % (facet.name, facet.type, datum))
                elif facet.type == 'Link':
                    t = facet.data[i] # has name, href
                    if t is not None:
                        out.write('\n  <Facet Name="%s"> <Link Name="%s" Href="%s"/> </Facet>' % (facet.name, t[0], t[1]))
                else:
                    out.write('\n  <Facet Name="%s"> '% facet.name)
                    d = facet.data[i]
                    if type(d)==types.ListType:
                        for x in d: out.write('<%s Value="%s"/>' %( facet.type, x))
                    else: 
                        out.write('<%s Value="%s"/>' %( facet.type, d))
                    out.write(' </Facet>' ) 
                
            out.write('\n </Facets>\n</Item>')    
        out.write('\n</Items>')
        
        out.write(Collection.trailer)
        out.close()
        
if __name__=='__main__':
    pass
    


