
# Standard Modules
import StringIO
import ConfigParser
import random


def grab_configtxt(config_location):

    '''
        Creates a parser that reads the config.txt. Establishes a section called [osmc]
    '''

    # open the config file read the contents into a long string
    with open(config_location,'r') as f:

        # add [root] to the front to create a root section for the parser to read
        long_string = '[osmc]\n' + f.read()

    # put the string into a stringIO to allow the parser to read it like a file
    long_string_file = StringIO.StringIO(long_string)
    
    # instantiate a config parser
    parser = ConfigParser.RawConfigParser()

    # read the stringIO into the config parser, file_config represents the previous config data
    parser.readfp(long_string_file)

    return parser



def read_config(config_location, parser_provided=False, return_the_parser=False):

    '''
        Reads the config and retrieves the settings in the form of a dict with the settings {name: value}
    '''

    # grab the parser if it isnt provided
    if parser_provided:
        parser = parser_provided
    else:
        parser = grab_configtxt(config_location)

    # retrieve all the settings in the config, in tuples with the settings (name, value)
    settings_raw = parser.items('osmc')

    settings = dict(settings_raw)

    if return_the_parser:
    
        return settings, parser

    else:

        return settings


def write_config(config_location, parser_provided=False, changes={}):

    '''
        Write the changes back to the config.txt.

        'changes' should be a dictionary with the setting name as the key, and the new setting value as the value.
        'changes' can also include a key 'remove', the value of which is a list with the settings to remove from the config file.
    '''

    # grab the parser if it isnt provided
    if parser_provided:
        blotter = parser_provided
    else:
        blotter = grab_configtxt(config_location)

    # force all data to be written as a string
    blotter.optionxform = str

    # loop through the changes and make the change to the config
    for setting, value in changes.iteritems():

        # if the setting is the remove list, then remove those entries from the config
        if setting == 'remove':

            for removal_candidate in changes.get('remove', []):

                blotter.remove_option('osmc', removal_candidate)

            continue
            
        # otherwise, write the new value to the setting
        blotter.set('osmc', setting, value)

    # create a stringIO to hold all the new settings
    long_string_file = StringIO.StringIO('')

    # pass the settings over to the long_string_file
    blotter.write(long_string_file)

    # skip the first seven characters to ignore "[osmc]\n" at the start of the file
    long_string_file.seek(7)

    # write the long_string_file to the config.txt
    with open(config_location,'w') as f:
        for line in long_string_file.readlines():
            f.write(line.replace(" = ","="))



def test():
    '''
        tester for read and write
    '''

    config_location = 'C:\\Temp\\config.txt'

    settings_dict = read_config(config_location)

    print settings_dict

    settings_dict['new_setting'] = 'farts'

    print settings_dict

    removes = []
    changes = {}

    for k, v in settings_dict.iteritems():

        if k == 'replace_this':

            removes.append(k)

            continue
        else:
            changes[k] = random.randint(0,500)


    for change, v in changes.iteritems():
        settings_dict[change] = v

    for remove in removes:
        del settings_dict[remove]

    settings_dict['remove'] = removes


    print settings_dict

    write_config(config_location, changes=settings_dict)




if ( __name__ == "__main__" ):

    test()










