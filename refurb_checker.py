from HTMLParser import HTMLParser
import urllib2
import smtplib

# Get source code for website of interest
url_link = urllib2.urlopen("http://store.apple.com/us/browse/home/specialdeals/mac/imac/27")
# print url_link.read()


class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.curState = 0           
        self.product_link = None    
        self.product_title = None   
        self.release_date = None   
        self.display = None         
        self.memory = None          
        self.price = None  
        self.states = { "LookForNewProdTag": 0,
                        "LookForNewProdLinkTag": 1,
                        "LookForTitleData": 2,
                        "LookForRelDateTag": 3,
                        "LookForRelDateData": 4,
                        "LookForDisplayData": 5,
                        "LookForMemoryData": 6,
                        "LookForPriceTag": 7,
                        "LookForPriceData": 8,
                        "EndState": 9 }         


    # This function looks for html start tags and does a "thing" when it finds one 
    # It should do nothing unless the curState is 0, 1, or 7 and the tag matches the specified criteria
    def handle_starttag(self, tag, attrs):
        # find the start tag at the beginning of a new product
        if self.curState == self.states["LookForNewProdTag"]:
            # checking tag for 'tr' and class="product" attributes
            # this is a unique combination that appears at the beginning of each new product
            if tag == 'tr' and attrs == [('class', 'product')]:
                print "Found product! Advancing state..."
                # advance state
                self.curState = self.states["LookForNewProdLinkTag"]   
        
        # find the tag containing the product link and store product link
        elif self.curState == self.states["LookForNewProdLinkTag"]:   
            if tag == 'a':
                for attribute in attrs:
                    if attribute[0] == 'href':
                        # set the product link to be the link in the tag attributes
                        self.product_link = attribute[1]    
                        print "Found link! Advancing state..."
                        # print self.product_link
                        # advance state
                        self.curState = self.states["LookForTitleData"]   

        # find the tag preceding the price - the price itself is data
        elif self.curState == self.states["LookForPriceTag"]:    
            if tag == 'span' and attrs == [('itemprop', 'price')]:
                print "Located price tag! Advancing state..."
                # advance state
                self.curState = self.states["LookForPriceData"]   

    
    # This function looks for html end tags and does a thing when it finds one
    def handle_endtag(self, tag):
        # need to find the end tag that immediately precedes the release date
        if self.curState == self.states["LookForRelDateTag"]:  
            if tag == 'p':
                print "Found the end tag! Advancing state..."
                # advance state
                self.curState = self.states["LookForRelDateData"]   

    
    # This function looks for data in the html code and does a thing when it finds some
    def handle_data(self, data):
        # find the title data
        if self.curState == self.states["LookForTitleData"]:  
            self.product_title = data.strip()
            print "Found title! Advancing state..."
            # print self.product_title
            # advance state
            self.curState = self.states["LookForRelDateTag"]   
        # elif self.curState == self.states["LookForRelDateTag"]:
        #   if len(data.strip()) == 0:
        #       print "There's empty data here!"
        
        # find the release date - want 2014 or newer
        elif self.curState == self.states["LookForRelDateData"]:    
            if ("2014" in data.split()) or ("2015" in data.split()):
                self.release_date = data.strip()
                print "Found release date! Advancing state..."
                # print self.release_date
                # advance state
                self.curState = self.states["LookForDisplayData"]   
            else:
                # if release date not current enough, set state to 0 to look for the next new product TAG
                self.curState = self.states["LookForNewProdTag"]   
        
        # find the display type - want retina display
        elif self.curState == self.states["LookForDisplayData"]:    
            if ("Retina" in data.split()) or ("retina" in data.split()):
                self.display = data.strip()
                print "Found Retina display!! Advancing state..."
                # print self.display
                # advance state
                self.curState = self.states["LookForMemoryData"]   
            else:
                # look for next new product tag if display is not retina
                self.curState = self.states["LookForNewProdTag"]   

        # find the product's memory - want 16GB
        elif self.curState == self.states["LookForMemoryData"]:    
            if "16GB" in data.split():
                self.memory = data.strip()
                print "Found 16GB memory! Advancing state..."
                # print self.memory
                # advance state
                self.curState = self.states["LookForPriceTag"]   
            else:
                # look for the next new product tag if memory isn't 16GB
                self.curState = self.states["LookForNewProdTag"]   

        # find the price - want to pay no more than $2500
        elif self.curState == self.states["LookForPriceData"]:   
            clean_data = data.translate(None, '$,').strip()
            # print clean_data
            self.price = float(clean_data)
            # print self.price
            if self.price <= 2500:
                print "Found a good price! Sending email!..."
                # print self.price
                # we found a matching product! advance to state 9 to do nothing with the rest of the html
                self.curState = self.states["EndState"]   
                self.product_match(self.product_link, self.product_title, self.release_date, self.display, self.memory, self.price)
            else:
                # if price doesn't match, set state to look for next new product tag
                self.curState = self.states["LookForNewProdTag"]   

    
    # This function takes a product match and sends an email alert
    def product_match(self, link, title, date, display, memory, price):
        # compile everything into a formatted string
        body_text = "Product: %s\n" % title
        body_text += "Release date: %s\n" % date
        body_text += "Display type: %s\n" % display
        body_text += "Memory: %s\n" % memory
        body_text += "Price: $%s\n" % price
        body_text += "Product link: http://store.apple.com%s\n" % link

        self.send_email("<toEmailAddress>@gmail.com", "Found a computer!", body_text)

        # print to terminal for funzies
        print "Product Match: %s" % title
        print date
        print display
        print memory
        print price
        print link

    
    # This function sets up how to send the email via gmail
    def send_email(self, rcvr_address, subject, body_text):
        server = smtplib.SMTP("smtp.gmail.com", 587)

        server.ehlo()
        server.starttls()
        server.login("<fromEmailAddress>@gmail.com", "password")   

        msg = "From: <fromEmailAddress>@gmail.com\r\n"
        msg += "To: %s\r\n" % rcvr_address
        msg += "Subject: %s\r\n" % subject
        msg += "\r\n%s" % body_text
        server.sendmail("<fromEmailAddress>@gmail.com", rcvr_address, msg)

        server.quit()


# ready set go!
parser = MyHTMLParser()
parser.feed(url_link.read())
