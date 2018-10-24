#!/usr/bin/python2.7
#Script to find untagged volumes. After that, the script will find the instance id attach to this volume, get the specified tag and add tag on volume
#Author: Alan Santos (alanwds@gmail.com)

#Import boto3 lib
import boto3
import sys
import os
from time import sleep

#if debbug is setted, will print everything  (produces a lot of information)
debug = int(os.getenv('DEBUG',0))

#If you will tag a lot of volumes, set sleep to a bigger value to skip rate limit
sleepTime = 0.5

def showHelp():
        print "Usage: ./script requiredTag"
        sys.exit(1)

def printMessage(message):
	if debug == 1:
		print message

#Function to find the volumes without the required tags
def findUntaggedVolumes(requiredTag):

	volumes = {}
	untaggedVolumes = []
	
	#Start boto client
	ec2 = boto3.client('ec2')

	printMessage("Searching for tag " + requiredTag)

	#Get all volumes
	for response in ec2.get_paginator('describe_volumes').paginate():
		#run the list with all volumes and get tags by tags
		for volume in response['Volumes']:
			tags = volume.get('Tags', [])

			#if tags is empty, we can set this volume without specified tag 
			if not tags:
				printMessage("Required tag is not founded on volume " + volume['VolumeId'] + ". Let's insert this volume id on untaggedVolumes list. To be honest, no tags are founded")
				untaggedVolumes.append(volume['VolumeId'])
			else:

				#Start a counter to use as validator
				found = 0
				#Run list with all tags returned
				for tagKey in tags:
					#check if required tag is here
					if tagKey["Key"] == requiredTag:
						printMessage("We found the tag " + requiredTag + " on " + volume['VolumeId'] + ": Value: " + tagKey["Value"])
						found = 1
						break

				#Check if there are no results on lists. If not, we have to put this VolumeId on untaggedList
				if found == 0:
					untaggedVolumes.append(volume['VolumeId'])
					printMessage("Required tag is not founded on volume " + volume['VolumeId'] + ". Let's insert this volume id on untaggedVolumes list")
				
	return untaggedVolumes

#Function to search the tags on instances. After that, will return a dict with all volumesIds and the tags that should be applyed for then 
def searchTagsOnInstances(volumesIdAndInstancesId,requiredTag):

	#Create a dictionary to store volumesIds and Tags
	volumesIdsAndTags = {}
	#get reservation objetc with all instances info
	ec2 = boto3.resource('ec2')

	printMessage("Starting function to apply the Tags")
	#Run the dictionary to get all volumes id and instances id
	for volumeId,instanceId in volumesIdAndInstancesId.items():
		printMessage("Dealing with volumeid: " + volumeId + " and instanceId: " + instanceId)
		#Get information about this instance
		ec2instance = ec2.Instance(instanceId)
		for tags in ec2instance.tags:
			if tags["Key"] == requiredTag:
				tagToSet = tags["Value"]
				printMessage("We found the required tag " + requiredTag + " on instance " + instanceId + "saving the value on it: " + tagToSet)
				#If found the tag, we should build a new dict with the volumesIds and tha tags
				volumesIdsAndTags.update({volumeId:tagToSet})

		#Sleep one second to avoid rate limit
		sleep(sleepTime)

	#After all, return the new dict with volumesIds and tags
	return volumesIdsAndTags

#Function to set tag on the volume
def setTagsOnVolumes(volumesIdsAndTags,requiredTag):

	#Create ec2 boto connection
	ec2 = boto3.resource('ec2')

	#Create a counter to know how much volumes recived tags
	counter = 0

	for volumeId,tagValue in volumesIdsAndTags.items():
		printMessage("Lets insert the tag " + requiredTag + " with value: " + tagValue + " on volume id: " + volumeId)

		#Add tag on volume. Use split to cast the string in a list, format accept by create_tags method
		ec2.create_tags(Resources=volumeId.split(), Tags=[{"Key" : requiredTag,"Value" : tagValue}])
		counter += 1
		sleep(sleepTime)
	return counter


def findInstancesIdsOfUntaggedVolumes(untaggedVolumes):

	#Create list for store intancesIds
	instancesIdsOfUntaggedVolumes = []

	#Create a dict with volumeId and instanceId
	volumesIdAndInstancesId = {}

	#Create boto connection
        ec2client = boto3.client('ec2')

	printMessage("Starting to look for instances ID")
	allVolumes = ec2client.describe_volumes()

	#Run all the volumes to get they instancesIds
	for volume in allVolumes['Volumes']:

		#Get the volumeID
		volumeId = volume['VolumeId']

		#Check if the volume id match with the untaggedVolumes list
		if volumeId in untaggedVolumes:
			printMessage("We found the instance id " + volume['Attachments'][0]['InstanceId'] +  " for volume " + volumeId)
			instanceId = volume['Attachments'][0]['InstanceId']

			#Add this tuple in dict
			volumesIdAndInstancesId.update({volumeId:instanceId})
		else:
			printMessage("The instance id " + volume['Attachments'][0]['InstanceId'] +  " isan't attach volume" + volumeId)
			
	
	return volumesIdAndInstancesId 

def main():

	print "Looking for env variable \"REQUIRED_TAG\""
	requiredTag = os.getenv('REQUIRED_TAG')

	if debug == 1:
		print "Starting script in DEBUG MODE"
	else:
		print "Starting script in NORMAL MODE"

        print "Looking for env variable \"REQUIRED_TAG\""
        requiredTag = os.getenv('REQUIRED_TAG')

	#check if env variable with required tag is setted
	if requiredTag is not None:
		print "Looking for tag ",requiredTag
	else:
		print "No env variable setted. Let's try the argument"
		#check if the parameters are sented
		if len(sys.argv) < 2 or len(sys.argv) > 2:
			showHelp()
		else:
			#Set the requiredTag as the recived parameter
			requiredTag = sys.argv[1]

	print "Searching for untaggedVolumes"
	#Get the untaggedVolumes and their instances Ids
	untaggedVolumes = findUntaggedVolumes(requiredTag)

	if len(untaggedVolumes) > 1:
		print "We found " + str(len(untaggedVolumes)) + " untagged volumes"
	else:
		print "No untagged volumes founded. Exiting..."
		sys.exit(0)

	print "Looking for associated instances to get tags..."
	#Get the instances Ids that should be used for looking tags
	volumesIdAndInstancesId = findInstancesIdsOfUntaggedVolumes(untaggedVolumes)

	print "Looking for the tags on the associated instances..."
	#Search for the tags on intances
	volumesIdsAndTags = searchTagsOnInstances(volumesIdAndInstancesId,requiredTag)

	if len(volumesIdsAndTags) <= 1:
		print "No tag founded on instances to get and add on volumes. Sorry. Exiting..."
		sys.exit(1)

	print "Tag volumes with tags from attached instances..."
	#Call function to tag volumes
	numberOfVolumesTagged = setTagsOnVolumes(volumesIdsAndTags,requiredTag)
	print "We tagged " + str(numberOfVolumesTagged) + " volumes"
	print "Congrats :)"

if __name__ == '__main__':
    main()
