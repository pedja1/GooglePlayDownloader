#!/usr/bin/python
#
# This file is part of GooglePlay Downloader.
#
# Copyright(c) 2012-2013 Simone Margaritelli aka evilsocket
# evilsocket@gmail.com
# http://www.evilsocket.net
#
# This file may be licensed under the terms of of the
# GNU General Public License Version 2 (the ``GPL'').
#
# Software distributed under the License is distributed
# on an ``AS IS'' basis, WITHOUT WARRANTY OF ANY KIND, either
# express or implied. See the GPL for the specific language
# governing rights and limitations.
#
# You should have received a copy of the GPL along with this
# program. If not, go to http://www.gnu.org/licenses/gpl.html
# or write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
import httplib, urllib, base64, zlib, re, optparse

class Market:
  LOGIN_HOST    = "www.google.com"
  LOGIN_PAGE    = "/accounts/ClientLogin"
  LOGIN_SERVICE = "androidsecure"
  LOGIN_TYPE    = "HOSTED_OR_GOOGLE"
  API_HOST      = "android.clients.google.com"
  API_PAGE      = "/market/api/ApiRequest"
  
  def __init__( self, email, password ):
    self.email    = email
    self.password = password
    self.token    = None
  
  def login( self ):			
    params = urllib.urlencode({
      "Email"       : self.email,
      "Passwd"      : self.password,
      "service"     : Market.LOGIN_SERVICE,
      "accountType" : Market.LOGIN_TYPE
    })
    
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    
    connection = httplib.HTTPSConnection( Market.LOGIN_HOST )
    
    connection.request("POST", Market.LOGIN_PAGE, params, headers )
    
    response = connection.getresponse().read()
    
    connection.close()

    if "Error" in response:
      raise Exception( "Invalid login credentials." )
      
    for line in response.split("\n"):
      if "Auth=" in line:
        self.token = line.split("=")[1]
    
    if self.token is None:
      raise Exception( "Unexpected response." )
      
  def get_asset( self, request ):
    params = urllib.urlencode({
      "version" : 2,
      "request" : request
    })
        
    headers = {"Content-type": "application/x-www-form-urlencoded"}
    
    connection = httplib.HTTPSConnection( Market.API_HOST )
    
    connection.request( "POST", Market.API_PAGE, params, headers )
    gzipped = connection.getresponse().read()
    
    connection.close()
    
    response = zlib.decompress( gzipped, 16 + zlib.MAX_WBITS )
    
    dl_url    = ""
    dl_cookie = ""
        
    match = re.search( "(https?:\/\/[^:]+)", response )
    
    if match is None:
      raise Exception( "Unexpected response." )
      
    else:
      dl_url = match.group(1)
    
    match = re.search( "MarketDA.*?(\d+)", response )
    
    if match is None:
      raise Exception( "Unexpected response." )
      
    else:
      dl_cookie = match.group(1)
      
    return dl_url + "#" + dl_cookie
      
class ProtocolBuffer:
  def __init__( self ):
    self.buffer = []
  
  def __encode_int( self, number ):
    while number:
      mod    = number % 128
      number >>= 7
      if number:
        mod += 128
        
      self.buffer.append( mod )

  def reset( self ):
    self.buffer = []
    
  def update( self, data, raw = False ):

    if raw is True:
      self.buffer.append( data )
    
    else:    
      data_type = type(data).__name__
      
      if data_type == "bool":
        self.buffer.append( 1 if data is True else 0 )
        
      elif data_type == "int":
        self.__encode_int( data )
      
      elif data_type == "str":
        self.__encode_int( len(data) )
        for c in data:
          self.buffer.append( ord(c) )
      
      else:
        raise Exception( "Unhandled data type : " + data_type )
        
    return self.buffer
    
  def finalize( self, b64 = True ):
    stream = ""
    for data in self.buffer:
      stream += chr( data )
      
    return stream if b64 is False else base64.b64encode( stream, "-_" )

class Operator:
  OPERATORS = {
    "Brazil" : {'TIM': '72402', 'Claro': '72405', 'Vivo': '72406', 'Oi': '72431'},
    "Canada" : {'MicroCell': '302370', 'Fido Canada': '30200001', 'Telus': '302220', 'Rogers A&T': '302720'},
    "Guinea-Bissau" : {'Orange': '63203', 'Arreba': '63202'},
    "Kuwait" : {'Viva': '41904', 'Wataniya': '41903', 'zain KW': '41902'},
    "Panama" : {'Claro': '71403', 'Cable & Wireless': '71401', 'Digicel': '71404', 'Movistar': '71402'},
    "Mali" : {'Orange': '61002', 'Malitel': '61001'},
    "Lithuania" : {'BITE': '24602', 'Tele 2': '24603', 'Omnitel': '24601'},
    "Costa Rica" : {'ICE': '71203'},
    "Cambodia" : {'Star-Cell': '45605', 'qb': '45604', 'Beeline': '45609', 'Smart Mobile': '45606', 'Mobitel': '45601', 'Metfone': '45608', 'hello': '45602', 'Mfone': '45618'},
    "Bahamas" : {'BaTelCo': '364390'},
    "Aruba" : {'SETAB': '36301', 'Digicel': '36302'},
    "Arab Emirates" : {'du': '42403', 'Etisalat': '42402'},
    "Ireland" : {'Eircom': '27207', 'Vodafone': '27201', 'O2': '27202', 'Meteor': '27203'},
    "Argentina" : {'Claro': '722330', 'Personnal': '722341', 'Nextel': '722020', 'Movistar': '722010'},
    "Bolivia" : {'Tigo': '73603', 'Nuavatel': '73601', 'Encel': '73602'},
    "Cameroon" : {'Orange': '62402', 'MTN Cameroon': '62401'},
    "Burkina Faso" : {'Telmob': '61301', 'Telecel Faso': '61303', 'Zain': '61302'},
    "Cote Ivore" : {'Koz': '61204', 'Moov': '61204'},
    "Czech Republic" : {'O2': '23002', 'Vodafone': '23003', 'T-Mobile': '23001'},
    "Bahrain" : {'VIVA': '42604', 'BaTelCo': '42601', 'zain BH': '42602'},
    "Saudi Arabia" : {'Mobily': '42003', 'Zain SA': '42004', 'Al Jawal': '42001'},
    "Australia" : {'Optus': '50502', 'OneTel': '50509', 'Vodafone': '50503', 'Telstra Mobile': '50502'},
    "Columbia" : {'Edatel': '732002', 'Comcel': '732101'},
    "Algeria" : {'Djezzy': '60302', 'Mobilis': '60301', 'Nedjma': '60303'},
    "El Salvador" : {'Claro': '70611', 'Tigo': '70603', 'Digicel': '70602', 'CTE Telecom': '70601', 'Movistar': '70604'},
    "Japan" : {'KDDI': '44008', 'SoftBank': '44004', 'DoCoMo': '44010', 'eMobile': '44000', 'TU-KA': '44081'},
    "Jordan" : {'Orange': '41677', 'Umniah': '41603', 'zain JO': '41601', 'Xpress Telecom': '41602'},
    "Slovenia" : {'Mobitel': '29341', 'Si.mobil': '29140', 'Tusmobil': '29370'},
    "Guatemala" : {'Claro': '70401', 'Comcel\\/Tigo': '70402', 'Movistar': '70403'},
    "Chile" : {'Claro': '73003', 'Nextel': '73009', 'Entel': '73001', 'Will': '73099', 'Movistar': '73002', 'VTR Movil': '73005'},
    "Belgium" : {'Mobistar': '20610', 'Base': '20620', 'Proximus': '20601', 'Telenet': '20605'},
    "Germany" : {'MobilCom': '26213', 'E-Plus': '26203', 'T-Mobile': '26201', 'Quam': '26214', 'O2': '26207', 'Vodafone': '26202'},
    "Haiti" : {'Digicel': '37202', 'Voila': '37201'},
    "Belize" : {'Digicell': '70267', 'Smart': '70299'},
    "Hong Kong" : {'New World PCS': '45410', 'HK Telecom': '45400', 'Smartone Mobile': '45406', 'Peoples Telephone': '45412', 'P Plus': '45422', 'Pacific Link': '45418', 'Hutchison': '45404', 'Mandarin Com.': '45416'},
    "Taiwan" : {'TransAsia': '46699', 'TINGSM': '46697', 'KG Telecom': '46688', 'TUNTEX': '46606', 'Chunghwa': '46692', 'Far Eastone': '46601', 'Mobitel': '46693'},
    "Spain" : {'Xfera': '21404', 'Telefonica': '21407', 'Amena': '21403', 'Vodafone': '21401', 'Movistar': '21402'},
    "Georgia" : {'Geocell': '28201', 'SILKNET': '28205', 'Iberiatel': '28203', 'Beeline': '28204', 'MagtiCom': '28202'},
    "Pakistan" : {'Zong': '41004', 'Ufone': '41003', 'Telenor': '41006', 'Warid': '41007', 'Mobilink': '41001', 'Vodafone': '41008'},
    "Denmark" : {'Orange': '23830', 'Debitel': '23800001', 'Telia Denmark': '23820', 'Denmark Mobil': '23801', 'Sonofon': '23802'},
    "Philippines" : {'Sun': '51505', 'Globe': '51502', 'Islacom': '51501', 'Smart': '51503'},
    "Vietnam" : {'3G EVNTelecom': '45208', 'S-Fone': '45203', 'Vietnam Mobile': '45205', 'EVNTelecom': '45206', 'Vinaphone': '45202', 'Beeline VN': '45207', 'MobiFone': '45201', 'Viettel Mobile': '45204'},
    "Turkmenistan" : {'MTS': '43801', 'TM-Cell': '43802'},
    "Moldova" : {'Orange': '25901', 'Moldcell': '25903', 'IDC': '25903'},
    "Morocco" : {'IAM': '60401', 'Meditel': '60400', 'INWI': '60402'},
    "Croatia" : {'Tele2': '21902', 'VIPNet': '21910', 'T-Mobile': '21901'},
    "Luxembourg" : {'Luxgsm': '27801', 'Orange': '27099', 'Tango': '27077'},
    "Antigua" : {'APUA': '344030', 'Digicel': '338050', 'LIME': '344920'},
    "Thailand" : {'Orange': '52010', 'GSM 1800': '52023', 'DTotal': '52018', 'AIS': '52001'},
    "Switzerland" : {'Orange': '22803', 'Swisscom': '22801', 'Sunrise': '22802'},
    "Honduras" : {'Claro': '70801', 'Digicel': '70840', 'Hondutel': '70830'},
    "New Zealand" : {'Telecom': '53000', 'Vodafone': '53001'},
    "Jamaica" : {'Claro': '338070', 'Digicel': '338050', 'LIME': '338180'},
    "Albania" : {'AMC': '27601', 'Plus': '27604', 'Vodafone': '27602', 'Eagle Mobile': '27603'},
    "Estonia" : {'EMT': '24801', 'Estonian Mobile': '24801', 'Tele 2': '24803', 'Elisa': '24802', 'RadioLinja': '24802'},
    "Uruguay" : {'Ancel': '74801', 'Claro': '74810', 'Movistar': '74807'},
    "Nicaragua" : {'Claro': '71021', 'Movistar': '71030'},
    "South Africa" : {'Vodacom': '65501', 'Cell C': '65507', 'MTN': '65510'},
    "India" : {'Escotel Mobile': '40412', 'TATA Cellular': '40407', 'Ina Spice': '40014', 'Hutch': '40405', 'Dolphin': '40468', 'Videocon': '40584', 'Idea': '40422', 'Usha Martin Tel.': '40426', 'Orange': '40020', 'Oasis': '40470', 'Bharti Telecom': '40402', 'Ushafon': '40408', 'Airtel Digilink': '40401', 'BSNL Mobile': '40455', 'INA AIRTel': '40440', 'Ushafone': '40432', 'BPL USWest': '40421', 'Spice': '40441'},
    "Azerbaijan" : {'Bakcell': '40002', 'Azercell': '40001', 'Nar Mobile': '40004', 'FONEX': '40003'},
    "Uzbekistan" : {'MTS': '73407', 'Ucell': '73405', 'Beeline': '73404'},
    "Tunisia" : {'Orange': '60501', 'Tunisiana': '60503', 'Tunicell': '60502'},
    "Rwanda" : {'Tigo': '63513', 'MTN': '63510'},
    "Colombia" : {'Tigo': '732111', 'Movistar': '732102'},
    "Burundi" : {'Omatel': '64203', 'Smart Mobile': '64207', 'Spacetel': '64201', 'Africell': '64202', 'U-COM Burundi': '64282'},
    "Kenya" : {'yu': '69305', 'Safaricom': '63902', 'Orange Kenya': '63907'},
    "South Korea" : {'SKT': '45005', 'Power 017': '45003', 'Olleh': '45008', 'LGT': '45006', 'KT': '45002'},
    "Cyprus" : {'MTN': '28010', 'Vodafone': '28001'},
    "Mamibia" : {'MTC': '64901', 'Switch': '64902', 'Leo': '64903'},
    "Turkey" : {'Avea': '28603', 'Turkcell': '28601', 'Vodafone': '28602'},
    "Qatar" : {'Qtel': '42701', 'Vodafone': '42702'},
    "Netherlands Antilles" : {'Telcell': '36251', 'UTS': '36291', 'Digicel': '36269', 'MIO': '36295', 'Bayos': '36294'},
    "Italy" : {'BLU': '22298', '3': '22299', 'Wind Tel.': '22288', 'Telecom Italia': '22201', 'Vodafone': '22210'},
    "Bangladesh" : {'TeleTalk': '47004', 'Gremenphone': '47001', 'CityCell': '47005', 'Banglalink': '47003', 'Warid Telecom': '47007', 'Airtel': '47006', 'Robi': '47002'},
    "USA" : {'Wireless 2000': '31011', 'Powertel': '31027', 'BellSouth': '31015', 'Aerial': '31031', 'Iowa Wireless': '31077', 'Western Wireless': '31026', 'Cingular': '31017', 'AT&T': '31038', 'Sprint': '31002', 'T-Mobile': '31020'},
    "Lebanon" : {'Ogero Mobile': '41505', 'Alfa': '41501', 'mtc touch': '41503'},
    "Hungary" : {'Westel GSM': '21630', 'Pannon GSM': '21601', 'Vodafone': '21670'},
    "Tanzania" : {'SasaTel': '64006', 'Vodacom': '64004', 'Life': '64007', 'tiGO': '64002', 'Zantel': '64003'},
    "Mongolia" : {'Skytel': '42891', 'Unitel': '42888', 'MobiCom': '42899', 'G-Mobile': '42898'},
    "France" : {'Bouygues Telecom': '20820', 'Orange': '20801', 'SFR': '20810'},
    "Netherlands" : {'Telfort': '20412', 'Tele 2': '20402', 'T-Mobile': '20416', '6GMobile': '20414', 'Vodafone': '20404', 'Orange': '20420', 'KPN': '20408'},
    "Slovakia" : {'Orange': '23101', 'O2': '23106', 'T-Mobile': '23102'},
    "Peru" : {'Claro': '71610', 'NEXTEL': '71607', 'Movistar': '21606'},
    "Laos" : {'Unitel': '45703', 'LaoTel': '45701', 'Tigo': '45708', 'ETL': '45702'},
    "Norway" : {'Telenor': '24201', 'NetCom': '24202'},
    "Nigeria" : {'M-TEL': '62140', 'Glo': '62150', 'MTN': '62130', 'Airtel': '62120', 'Etsalat': '62160'},
    "Benin" : {'Moov': '61602', 'Libercom': '61601', 'MTN': '61603', 'BBCOM': 'BBCOM', 'Glo': '61605'},
    "Israel" : {'Orange': '42501', 'JAWAL': '42505', 'Cellcom': '42502'},
    "Singapore" : {'StarHub': '52205', 'GSM 900': '52501', 'GSM 1800': '52502', 'MobileOne Asia': '52503', 'M1-3GSM': '52504'},
    "Iceland" : {'Simmin': '27401', 'Vodafone': '27402'},
    "Senegal" : {'Orange': '60801', 'Expresso': '60803', 'Tigo': '60802'},
    "Papua New Guinea" : {'B-Mobile': '53701', 'Digicel': '53703'},
    "Togo" : {'Togo Cell': '61501', 'Moov': '61503'},
    "Trinidad and Tobago" : {'Digicel': '37413', 'Bmobile': '37412'},
    "China" : {'China Telecom': '46005', 'China Tietong': '46020', 'China Mobile': '46000', 'China Unicom': '46001'},
    "Ecuador" : {'Porta': '74001', 'Alegro': '74002', 'Movistar': '74000'},
    "Armenia" : {'Orange': '28310', 'VivaCell': '28305', 'Beeline': '28301'},
    "Oman" : {'Oman Mobile': '41202', 'Nawras': '42203'},
    "Tajikistan" : {'Babilon-M': '43604', 'Beeline': '43605', 'MLT': '43603', 'Tcell': '43602'},
    "Dominican Republic" : {'Orange': '37001', 'Tricom': '37003', 'Claro': '37002', 'Viva': '37004'},
    "Kazakhstan" : {'Beeline': '40101', 'Kcell': '40102'},
    "Poland" : {'ERA GSM': '26002', 'IDA Centertel': '26003', 'Play': '26006', 'Polkomtel PLUS': '26001'},
    "Ukraine" : {'MTS': '25501', 'kylvstar': '25503', 'Beeline': '25502', 'Life': '25507'},
    "Ghana" : {'tiGO': '62003', 'MTN': '62001', 'Airtel': '62006', 'Vodafone': '62002'},
    "Kyrgyzstan" : {'MegaCom': '43705', 'Beeline': '43701', 'O': '43709', 'Fonex': '43703'},
    "Indonesia" : {'Ceria': '51027', 'XL': '51011', 'StarOne': '51003', 'TELKOMMobile': '51020', 'PSN': '51000', 'SMART': '51009', 'AXIS': '51008', 'TelkomFlexi': '51007', 'Fren\\/Hepi': '51028', '3': '51089', 'Telkomsel': '51010', 'INDOSAT': '51001'},
    "Finland" : {'Radjolinja': '24405', 'Finnet Group': '24409', '2G': '24412', 'Telia Finland': '24403', 'Sonera Corp.': '24409', 'AMT': '24414'},
    "Macedonia" : {'VIP MK': '29403', 'T-Mobile MK': '29401', 'ONE': '29402'},
    "Sri Lanka" : {'Mobitel': '41301', 'Hutch': '41308', 'Etisalat': '41303', 'Airtel': '41305', 'Dialog': '41302'},
    "Sweden" : {'Orange': '24003', 'Vodafone': '24008', '3 Sweden': '24002', 'Telia Mobitel': '24001', 'Comviq': '24007'},
    "Belarus" : {'MTS': '25702', 'Life': '25704', 'Velcom': '25701', 'DIALLOG': '25703'},
    "Cap Verde" : {'T+': '62502', 'CVMOVEL': '62501'},
    "Nepal" : {'Sky\\/C-Phone': '42903', 'SmartCell': '42904', 'Ncell': '42904', 'Namaste\\/NT Mobile': '42901'},
    "Russia" : {'North Caucasian': '25044', 'Megafon': '25002', 'BeeLine': '25099', 'New Telephone Cy': '25012', 'Don Telecom': '25010', 'MTS Moscow': '25001', 'Uratel': '25039', 'Kuban GSM': '25213', 'Zao Smarts': '25007', 'Siberian Cellular': '25005'},
    "Bulgaria" : {'M-Tel': '28401', 'Vivatel': '28401', 'Globul': '28405'},
    "Romania" : {'Mobifon': '22601', 'Cosmorom': '22603', 'Mobil Rom': '22610'},
    "Angola" : {'Unitel': '63102'},
    "Portugal" : {'Telecom Moveis': '26806', 'Optimus Telecom': '26803', 'Vodafone': '26801'},
    "Mexico" : {'Telcel': '33402', 'Lusacell': '33405', 'Nextel': '33401', 'Movistar': '33403'},
    "Egypt" : {'Etisalat': '60203', 'Vodafone': '60202', 'Mobinil': '60201'},
    "Fiji" : {'Digicel': '54202', 'Vodafone': '54201'},
    "Serbia" : {'Telenor': '22001', 'VIP Mobile': '22005', 'Telekom Srbija': '22003'},
    "Botswana" : {'Orange': '65202', 'Mascom': '65201', 'BTC Mobile': '65203'},
    "United Kingdom" : {'3': '23420', 'Manx Pronto': '23450', 'Orange': '23433', 'Jersey Telecom': '23450', 'Guermsey Tel.': '23455', 'O2': '23410', 'Vodafone': '23415', 'T-Mobile': '23430'},
    "Malaysia" : {'Celcom': '50219', 'U Mobilz': '50218', 'Maxis': '50212', 'DiGi': '50216', 'TM CDMA': '50201'},
    "Austria" : {'Mobilkom': '23101', 'Tele.ring': '23205', 'T-Mobile': '23203', '3AT': '23210'},
    "Latvia" : {'Tele 2': '24702', 'Latvian Mobile': '24701'},
    "Mozambique" : {'Vodacom': '64304', 'mCel': '64301'},
    "Uganda" : {'Orange': '64114', 'MTN': '64110', 'Zain': '64101', 'Warid Telecom': '64122'},
    "Greece" : {'Telestet': '20210', 'Cosmote': '20201', 'Wind': '20209', 'Vodafone': '20205'},
    "Paraguay" : {'Personal': '74405', 'Claro': '74402', 'Tigo': '74404', 'VOX': '74406'},
    "Gabon" : {'Liberts': '62801', 'Azur': '62804', 'Airtel': '62803', 'Moov': '62802'},
    "Niger" : {'Orange': '61404', 'Airtel': '61402', 'SahelCom': '61401', 'Telecel': '61403'},
    "Bosnia-Herzegovina" : {'BH Mobile': '21890', 'm:tel': '21805', 'HT-ERONET': '21803'}  
  }
  
  def __init__( self, country, name ):
    self.country = country
    self.name    = name
    self.code    = Operator.OPERATORS[country][name]    
      
class AssetRequest:
  def __init__( self, package_name, auth_token, device_id, operator, device_name, sdk_version):
    self.encode_table       = [0, [16], 2, [24], 4, [34], 6, [42], 8, [50], 10, [58], 12, [66], 14, [74], 16, [82], 18, [90], 20, [19, 82], 22, [10], 24, [20]]
    self.pad                = [ 10 ]
    self.buffer             = ProtocolBuffer()
    
    self.auth_token         = auth_token
    self.is_secure          = True
    self.sdk_version        = 2009011
    self.device_id          = device_id
    self.device_name        = device_name
    self.sdk_version        = sdk_version
    self.locale             = "en"
    self.country            = "us"
    self.operator_alpha     = operator.name
    self.sim_operator_alpha = operator.name
    self.operator_code      = operator.code
    self.sim_operator_code  = operator.code
    self.package_name       = package_name
    
  def encode( self ):
    self.buffer.reset()

    header_len = 0
    
    for encoder in self.encode_table:
      enc_type = type(encoder).__name__
      
      if enc_type == "list":
        self.buffer.buffer += encoder
      
      elif enc_type == "int":
        if encoder ==  0:
          self.buffer.update( self.auth_token )
            
        elif encoder ==  2:
          self.buffer.update( self.is_secure )
            
        elif encoder ==  4:
          self.buffer.update( self.sdk_version )
            
        elif encoder ==  6:
          self.buffer.update( self.device_id )
            
        elif encoder ==  8:
          self.buffer.update( '%s:%d' % (self.device_name, self.sdk_version) )
            
        elif encoder ==  10:
          self.buffer.update( self.locale )
            
        elif encoder ==  12:
          self.buffer.update( self.country )
            
        elif encoder ==  14:
          self.buffer.update( self.operator_alpha )
            
        elif encoder ==  16:
          self.buffer.update( self.sim_operator_alpha )
            
        elif encoder ==  18:
          self.buffer.update( self.operator_code )
            
        elif encoder ==  20:
          self.buffer.update( self.sim_operator_code )
          header_len = len( self.buffer.buffer ) + 1
          
        elif encoder ==  22:
          self.buffer.update( len( self.package_name ) + 2 )
                      
        elif encoder ==  24:
          self.buffer.update( self.package_name )
    
    self.buffer.buffer = self.pad + ProtocolBuffer().update( header_len ) + self.pad + self.buffer.buffer    
     
    return self.buffer.finalize()

if __name__ == '__main__':
  try:
    
    print( "\n\tGooglePlay Downloader - Directly download apks from GooglePlay to your PC.\n" +
               "\tCopyleft Simone Margaritelli <evilsocket@evilsocket.net>\n" +
               "\thttp://www.evilsocket.net\n\n" );
  
    parser = optparse.OptionParser( usage = "usage: %prog [options]\n\n" + 
                                            "EXAMPLE:\n" +
                                            "\t%prog --email your-email@gmail.com --password your-password --name com.arttech.xbugsfree --country \"Italy\" --operator \"3\" --device your-device-id"
    )
    
    parser.add_option( "-e", "--email",    action="store",  dest="email",    default=None, help="Your android account email.")
    parser.add_option( "-p", "--password", action="store",  dest="password", default=None, help="Your android account password.")
    parser.add_option( "-n", "--name",     action="store",  dest="package",  default=None, help="Package identifier ( com.something.name ).")
    parser.add_option( "-c", "--country",  action="store",  dest="country",  default=None, help="Your country.")
    parser.add_option( "-o", "--operator", action="store",  dest="operator", default=None, help="Your phone operator.")
    parser.add_option( "-d", "--device",   action="store",  dest="device",   default=None, help="Your device ID ( can be obtained with this app https://play.google.com/store/apps/details?id=com.redphx.deviceid ) .")
    parser.add_option( "-s", "--sdklevel", action="store",  type="int", dest="sdklevel", default=9, help="Android SDK API level (default is 9 like Android 2.3.1).")
    parser.add_option( "-m", "--devname",  action="store",  dest="devname",  default="passion", help="Device name (default 'passion' like HTC Passion aka Google Nexus One.")

    (o,args) = parser.parse_args()
  
    if o.email is None:
      print "No email specified." 
      
    elif o.password is None:
      print "No password specified." 
      
    elif o.package is None:
      print "No package specified." 
    
    elif o.country is None or o.country not in Operator.OPERATORS:
      print "Empty or invalid country specified, choose from : \n\n" + ", ".join( Operator.OPERATORS.keys() )

    elif o.operator is None or o.operator not in Operator.OPERATORS[ o.country ]:
      print "Empty or invalid operator specified, choose from : \n\n" + ", ".join( Operator.OPERATORS[ o.country ].keys() )
      
    elif o.device is None:
      print "No device id specified." 
    
    elif o.sdklevel < 2:
      print "The SDK API level cannot be less than 2."
      
    else:
      print "@ Logging in ..."
      
      market = Market( o.email, o.password )
      market.token = "@ adsafdsf"
      #market.login()
      
    print "@ Requesting package ..."
  
    operator = Operator( o.country, o.operator )
    #print operator
    request  = AssetRequest( o.package, market.token, o.device, operator, o.devname, o.sdklevel )
    #asset    = market.get_asset( request.encode() )  
    print request .encode()
    #print "@ Download %s from :\n  %s" % ( o.package, asset )
    
  except Exception as e:
    print e
