/**
 * SelectAction Component.
 */

 import React from 'react';
 import {
	 TouchableOpacity,
 } from 'react-native';
 import {
	 InputContext,
	 InputContextConsumer
 } from '../../utils/context';
 import * as Constants from '../../utils/constants';
 import * as Utils from '../../utils/util';
 
 export class SelectAction extends React.Component {
 
	 static contextType = InputContext;
 
	 constructor(props) {
		 super(props);
 
		 this.payload = this.props.selectActionData;
		 this.onExecuteAction = undefined;
		 this.inputArray = undefined;
		 this.toggleVisibilityForElementWithID = undefined;
		 this.addResourceInformation = undefined;
	 }
 
	 /**
	  * @description Invoked on tapping the button component
	  */
	 onClickHandle() {
		 let actionPayload = { ... this.payload };
		 switch (actionPayload.type) {
			 case Constants.ActionSubmit:
			 case Constants.ActionExecute:
				 actionPayload.data = this.getMergeObject();
				 /*
				  actionPayload already has `ignoreInputValidation` but to support 
				  backward compatibility we are passing it explicitly
				 **/
				 this.onExecuteAction(actionPayload, actionPayload.ignoreInputValidation);
				 break;
			 case Constants.ActionOpenUrl:
				 if (!Utils.isNullOrEmpty(this.props.selectActionData.url)) {
					 actionPayload.url = this.props.selectActionData.url;
					 this.onExecuteAction(actionPayload);
				 }
				 break;
			 case Constants.ActionToggleVisibility:
				 this.toggleVisibilityForElementWithID(this.props.selectActionData.targetElements);
				 break;
			 default:
				 //As per the AC schema, ShowCard action type is not supported by selectAction.
				 if (actionPayload.type != Constants.ActionShowCard) {
					 //Pass complete payload for all other types. 
					 actionPayload.data = this.getMergeObject();
					 this.onExecuteAction(actionPayload);
				 }
				 break;
		 }
	 }
	 getMergeObject = () => {
		 let mergedObject = {};
		 for (const key in this.inputArray) {
			 mergedObject[key] = this.inputArray[key].value;
		 }
		 if (this.data !== null) {
			 if (this.data instanceof Object)
				 mergedObject = { ...mergedObject, ...this.data }
			 else
				 mergedObject["actionData"] = this.data;
		 }
		 return mergedObject;
	 }
	 render() {
		 if (!this.props.configManager.hostConfig.supportsInteractivity) {
			 return null;
		 }
 
		 this.payload = this.props.selectActionData;
		 this.onExecuteAction = undefined;
		 this.toggleVisibilityForElementWithID = undefined;
 
		 const ButtonComponent = TouchableOpacity;
		 return (<InputContextConsumer>
			 {({ onExecuteAction, inputArray, addResourceInformation, toggleVisibilityForElementWithID }) => {
				 this.inputArray = inputArray;
				 this.onExecuteAction = onExecuteAction;
				 this.addResourceInformation = addResourceInformation;
				 this.toggleVisibilityForElementWithID = toggleVisibilityForElementWithID;
				 return <ButtonComponent
					 opacity={this.props.opacity}
					 onPress={() => { this.onClickHandle() }}
					 disabled={this.payload.isEnabled === undefined ? false : !this.payload.isEnabled}
					 accessible={true}
					 accessibilityLabel={this.payload.altText}
					 accessibilityRole={Constants.Button}
					 accessibilityState={{ disabled: this.payload.isEnabled === undefined ? false : !this.payload.isEnabled }}
					 style={this.props.style}>
					 <React.Fragment>{this.props.children}</React.Fragment>
				 </ButtonComponent>
			 }}
		 </InputContextConsumer>);
	 }
 }
 
 